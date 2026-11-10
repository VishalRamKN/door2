// door2 bottle-drop door: ESP32 (38-pin DevKit) firmware
// 2 x MG995 continuous-rotation servos (one per leaf) + 4 x KW11 limit switches.
//
// Works with ESP32 Arduino core 2.x and 3.x. No extra libraries.
// Serial monitor 115200, line ending "Newline". Type ? for the command list.
//
// Wiring (see ../WIRING.md):
//   Servo signal  L -> GPIO18   R -> GPIO19
//   Switches (COM -> GND, NC -> GPIO; pressed = HIGH, broken wire = "pressed" = safe)
//     L open -> GPIO32   L closed -> GPIO33   R open -> GPIO25   R closed -> GPIO26
//   Optional push button GPIO27 -> GND (open / close / stop)
//
// FIRST RUN: leave the pinions off the racks (or the leaves free), then
//   1. "n"  : sends the stop pulse for 10 s. If a servo creeps, turn its trim pot
//             (or change STOP_US_L/R below) until it stands still.
//   2. "L+" : left servo jogs a little in the + direction. Watch which way the
//             leaf would go. If + is OPEN set OPEN_SIGN_L = +1, else -1. Same for "R+".
//   3. "?"  : press each switch lever by hand and check its state changes.
//   4. Only then "o" / "c".

#include <Arduino.h>

// ---------------- pins ----------------
const int PIN_SERVO_L     = 18;
const int PIN_SERVO_R     = 19;
const int PIN_SW_L_OPEN   = 32;
const int PIN_SW_L_CLOSED = 33;
const int PIN_SW_R_OPEN   = 25;
const int PIN_SW_R_CLOSED = 26;
const int PIN_BUTTON      = 27;   // optional, to GND
const int PIN_LED         = 2;    // on-board LED: on while moving, blinks on a fault

// ---------------- tuning ----------------
// Switch wiring: true = NC contact used (pressed reads HIGH). false = NO contact (pressed reads LOW).
const bool SW_USE_NC = true;

// Servo pulse widths in microseconds. 1500 = stop on most MG995 360s; trim per servo.
const int STOP_US_L = 1500;
const int STOP_US_R = 1500;

// Which pulse direction opens each leaf: +1 = pulse above STOP opens, -1 = below. Find with L+/R+.
// The two servos are mirror images, so these are normally opposite.
const int OPEN_SIGN_L = -1;
const int OPEN_SIGN_R = +1;

// Speed as an offset from STOP (0..500 us). 500 = full speed (~60 rpm = ~56 mm/s of leaf).
// Start slow: the open switch trips ~1.5 mm before the hard stop.
const int SPEED_US     = 220;
const int JOG_SPEED_US = 150;
const unsigned long JOG_MS = 200;

const unsigned long MOVE_TIMEOUT_MS   = 4000;  // 69 mm at the slow speed takes ~2.5 s; raise if you lower SPEED_US
const unsigned long RELEASE_CHECK_MS  = 800;   // leaving a switch must release it within this time
const unsigned long CLOSE_EXTRA_MS    = 0;     // run on after the closed switch trips (seam gap), e.g. 80
const unsigned long OPEN_EXTRA_MS     = 0;     // run on after the open switch trips (keep 0: hard stop is close)
const unsigned long DETACH_AFTER_MS   = 150;   // stop pulse held this long, then PWM off (servo goes limp, no creep)
const int DEBOUNCE_READS = 3;                  // consecutive equal reads (1 ms apart) to accept a switch change

// ---------------- servo PWM (core 2.x and 3.x) ----------------
#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 2
#endif
const int PWM_FREQ = 50;
const int PWM_BITS = 16;

struct Servo360 {
  int pin, channel;
  bool attached = false;
  static uint32_t usToDuty(int us) { return (uint32_t)((uint64_t)us * ((1UL << PWM_BITS) - 1) / 20000UL); }
  void attach() {
    if (attached) return;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcAttach(pin, PWM_FREQ, PWM_BITS);
#else
    ledcSetup(channel, PWM_FREQ, PWM_BITS);
    ledcAttachPin(pin, channel);
#endif
    attached = true;
  }
  void writeUs(int us) {
    attach();
    us = constrain(us, 900, 2100);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcWrite(pin, usToDuty(us));
#else
    ledcWrite(channel, usToDuty(us));
#endif
  }
  void detach() {
    if (!attached) return;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcDetach(pin);
#else
    ledcDetachPin(pin);
#endif
    attached = false;
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);   // no pulses = MG995 idle
  }
};

// ---------------- debounced switch ----------------
struct Switch {
  int pin;
  const char *name;
  bool state = false;   // true = pressed
  int count = 0;
  bool raw() { return (digitalRead(pin) == HIGH) == SW_USE_NC; }
  void begin() { pinMode(pin, INPUT_PULLUP); state = raw(); }
  void update() {
    bool r = raw();
    if (r == state) { count = 0; return; }
    if (++count >= DEBOUNCE_READS) { state = r; count = 0; }
  }
};

// ---------------- leaf ----------------
enum Dir { NONE = 0, OPENING = 1, CLOSING = 2 };

struct Leaf {
  const char *name;
  Servo360 servo;
  Switch swOpen, swClosed;
  int stopUs, openSign;
  Dir dir = NONE;
  bool done = true;              // reached its switch for the current move
  bool overrun = false;          // switch tripped, running CLOSE/OPEN_EXTRA_MS
  bool releaseChecked = false;
  bool startedOnSwitch = false;
  bool sourceFreeSeen = false;   // the switch it is moving away from has been free during this move
  unsigned long tStart = 0, tTrip = 0, tStop = 0;
  bool pendingDetach = false;

  Switch &target() { return dir == OPENING ? swOpen : swClosed; }
  Switch &source() { return dir == OPENING ? swClosed : swOpen; }

  void drive(int sign, int speed) { servo.writeUs(stopUs + sign * speed); pendingDetach = false; }
  void halt() {
    servo.writeUs(stopUs);
    tStop = millis();
    pendingDetach = true;
    done = true;
    overrun = false;
  }
  void service() {
    if (pendingDetach && millis() - tStop >= DETACH_AFTER_MS) { servo.detach(); pendingDetach = false; }
  }
};

Leaf L, R;
Leaf *leaves[2] = {&L, &R};

enum State { IDLE, MOVING, JOGGING, NEUTRAL, FAULT };
State state = IDLE;
Dir moveDir = NONE;
unsigned long tMove = 0;
String faultMsg;

// ---------------- helpers ----------------
const char *swStr(Switch &s) { return s.state ? "PRESSED" : "free"; }

const char *leafPos(Leaf &l) {
  if (l.swOpen.state && l.swClosed.state) return "BOTH SWITCHES PRESSED (wire off?)";
  if (l.swOpen.state) return "OPEN";
  if (l.swClosed.state) return "CLOSED";
  return "between";
}

void stopAll() {
  for (Leaf *l : leaves) { l->halt(); l->dir = NONE; }
  state = IDLE;
  moveDir = NONE;
}

void fault(const String &msg) {
  stopAll();
  state = FAULT;
  faultMsg = msg;
  Serial.printf("FAULT: %s\n  Fix it, then send r to clear.\n", msg.c_str());
}

void printStatus() {
  const char *st[] = {"IDLE", "MOVING", "JOGGING", "NEUTRAL", "FAULT"};
  Serial.printf("state %s%s%s\n", st[state], state == FAULT ? ": " : "", state == FAULT ? faultMsg.c_str() : "");
  for (Leaf *l : leaves)
    Serial.printf("  %s leaf: %-8s  open sw %-7s  closed sw %-7s\n", l->name, leafPos(*l), swStr(l->swOpen), swStr(l->swClosed));
}

void printHelp() {
  Serial.println(F(
    "commands:\n"
    "  o        open both leaves\n"
    "  c        close both leaves\n"
    "  s        stop\n"
    "  ?        status (switches + state), and this help\n"
    "  r        clear a fault\n"
    "  L+ L-    jog left servo + / - (short, slow; ignores switches)\n"
    "  R+ R-    jog right servo\n"
    "  n        neutral test: stop pulse for 10 s (trim pots / STOP_US)\n"
    "  button on GPIO27: open if closed, close otherwise, stop while moving"));
}

void startMove(Dir d) {
  if (state == FAULT) { Serial.println("in FAULT, send r first"); return; }
  for (Leaf *l : leaves)
    if (l->swOpen.state && l->swClosed.state) { fault(String(l->name) + " leaf: both switches read pressed (check wiring)"); return; }

  moveDir = d;
  tMove = millis();
  state = MOVING;
  bool any = false;
  for (Leaf *l : leaves) {
    l->dir = d;
    l->overrun = false;
    l->releaseChecked = false;
    l->startedOnSwitch = l->source().state;
    l->sourceFreeSeen = !l->startedOnSwitch;
    if (l->target().state) { l->done = true; continue; }   // already there
    l->done = false;
    l->tStart = millis();
    int sign = (d == OPENING) ? l->openSign : -l->openSign;
    l->drive(sign, SPEED_US);
    any = true;
  }
  Serial.println(d == OPENING ? "opening..." : "closing...");
  if (!any) { Serial.println("already there"); stopAll(); }
}

void startJog(Leaf &l, int sign) {
  if (state == MOVING) { Serial.println("busy"); return; }
  if (state == FAULT) Serial.println("(jogging in FAULT state)");
  l.drive(sign, JOG_SPEED_US);
  l.tStart = millis();
  l.dir = NONE;
  l.done = false;
  if (state != FAULT) state = JOGGING;
  Serial.printf("jog %s %c  (pulse %d us)\n", l.name, sign > 0 ? '+' : '-', l.stopUs + sign * JOG_SPEED_US);
}

// ---------------- move supervision ----------------
void serviceMove() {
  unsigned long now = millis();
  bool allDone = true;
  for (Leaf *l : leaves) {
    if (l->done) continue;
    allDone = false;

    // left the start switch?
    // wrong way: ran into the switch it should be moving away from -> stop at once
    if (!l->source().state) l->sourceFreeSeen = true;
    else if (l->sourceFreeSeen) {
      fault(String(l->name) + " leaf went the WRONG WAY (hit its " + (moveDir == OPENING ? "closed" : "open") +
            " switch): flip OPEN_SIGN_" + (l == &L ? "L" : "R") + " and re-upload");
      return;
    }

    if (l->startedOnSwitch && !l->releaseChecked && now - l->tStart > RELEASE_CHECK_MS) {
      l->releaseChecked = true;
      if (l->source().state) {
        fault(String(l->name) + " leaf did not leave its " + (moveDir == OPENING ? "closed" : "open") +
              " switch (wrong OPEN_SIGN? pinion slipping? jammed?)");
        return;
      }
    }

    if (!l->overrun && l->target().state) {
      l->tTrip = now;
      unsigned long extra = (moveDir == CLOSING) ? CLOSE_EXTRA_MS : OPEN_EXTRA_MS;
      if (extra == 0) {
        l->halt();
        Serial.printf("  %s leaf %s (%lu ms)\n", l->name, moveDir == OPENING ? "open" : "closed", now - l->tStart);
        continue;
      }
      l->overrun = true;
    }
    if (l->overrun) {
      unsigned long extra = (moveDir == CLOSING) ? CLOSE_EXTRA_MS : OPEN_EXTRA_MS;
      if (now - l->tTrip >= extra) {
        l->halt();
        Serial.printf("  %s leaf %s (%lu ms)\n", l->name, moveDir == OPENING ? "open" : "closed", now - l->tStart);
      }
      continue;
    }

    if (now - l->tStart > MOVE_TIMEOUT_MS) {
      fault(String(l->name) + " leaf timeout: switch never tripped (" + String(MOVE_TIMEOUT_MS) + " ms)");
      return;
    }
  }
  if (allDone) {
    Serial.println(moveDir == OPENING ? "OPEN" : "CLOSED");
    stopAll();
  }
}

// ---------------- serial + button ----------------
void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  String c = cmd;
  c.toLowerCase();
  if (c == "o") startMove(OPENING);
  else if (c == "c") startMove(CLOSING);
  else if (c == "s") { stopAll(); Serial.println("stopped"); }
  else if (c == "?" || c == "h") { printStatus(); printHelp(); }
  else if (c == "r") { if (state == FAULT) { state = IDLE; faultMsg = ""; } Serial.println("fault cleared"); printStatus(); }
  else if (c == "l+") startJog(L, +1);
  else if (c == "l-") startJog(L, -1);
  else if (c == "r+") startJog(R, +1);
  else if (c == "r-") startJog(R, -1);
  else if (c == "n") {
    if (state == MOVING) { Serial.println("busy"); return; }
    for (Leaf *l : leaves) l->drive(0, 0);
    tMove = millis();
    state = NEUTRAL;
    Serial.printf("neutral test 10 s: L %d us, R %d us. Servos should stand still.\n", STOP_US_L, STOP_US_R);
  }
  else Serial.printf("unknown command '%s', send ? for help\n", cmd.c_str());
}

void serviceSerial() {
  static String buf;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { handleCommand(buf); buf = ""; }
    else if (buf.length() < 32) buf += ch;
  }
}

void serviceButton() {
  static bool last = HIGH;
  static unsigned long tChange = 0;
  static bool stable = HIGH;
  bool r = digitalRead(PIN_BUTTON);
  if (r != last) { last = r; tChange = millis(); }
  if (millis() - tChange > 30 && r != stable) {
    stable = r;
    if (stable == LOW) {   // pressed
      if (state == MOVING) { stopAll(); Serial.println("stopped (button)"); }
      else if (L.swClosed.state && R.swClosed.state) startMove(OPENING);
      else startMove(CLOSING);
    }
  }
}

// ---------------- setup / loop ----------------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  L.name = "left";  L.servo.pin = PIN_SERVO_L; L.servo.channel = 0; L.stopUs = STOP_US_L; L.openSign = OPEN_SIGN_L;
  R.name = "right"; R.servo.pin = PIN_SERVO_R; R.servo.channel = 2; R.stopUs = STOP_US_R; R.openSign = OPEN_SIGN_R;
  L.swOpen.pin = PIN_SW_L_OPEN;  L.swClosed.pin = PIN_SW_L_CLOSED;
  R.swOpen.pin = PIN_SW_R_OPEN;  R.swClosed.pin = PIN_SW_R_CLOSED;
  for (Leaf *l : leaves) {
    l->swOpen.begin();
    l->swClosed.begin();
    l->servo.detach();   // signal LOW: servos idle until a command
  }
  delay(300);
  Serial.println("\ndoor2 ready. Does nothing until you send a command.");
  printStatus();
  printHelp();
}

void loop() {
  static unsigned long tRead = 0;
  if (millis() - tRead >= 1) {
    tRead = millis();
    for (Leaf *l : leaves) { l->swOpen.update(); l->swClosed.update(); }
  }

  serviceSerial();
  serviceButton();

  switch (state) {
    case MOVING:  serviceMove(); break;
    case JOGGING:
    case FAULT: {
      bool jogging = false;
      for (Leaf *l : leaves) {
        if (!l->done && millis() - l->tStart >= JOG_MS) l->halt();
        if (!l->done) jogging = true;
      }
      if (state == JOGGING && !jogging) state = IDLE;
      break;
    }
    case NEUTRAL:
      if (millis() - tMove >= 10000) { stopAll(); Serial.println("neutral test done"); }
      break;
    default: break;
  }
  for (Leaf *l : leaves) l->service();

  // LED: on while moving, fast blink on fault
  if (state == FAULT) digitalWrite(PIN_LED, (millis() / 150) % 2);
  else digitalWrite(PIN_LED, state == MOVING || state == JOGGING);
}
