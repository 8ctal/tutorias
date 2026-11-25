#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <OneWire.h>
#include <DallasTemperature.h>

constexpr uint8_t TEMP_PIN = 4, TRIG_PIN = 18, ECHO_PIN = 19, BUTTON_PIN = 27;
constexpr float INVALID = -9999.0f;
OneWire bus(TEMP_PIN);
DallasTemperature thermometer(&bus);
Adafruit_MPU6050 mpu;
bool mpuReady = false;
uint8_t mpuAddress = 0x68;
bool mpuCompatible72 = false;
DeviceAddress temperatureAddress;
bool temperatureReady = false;
uint32_t conversionStarted = 0, lastMpuRetry = 0;
bool buttonPressed = false, lastRawButton = false;
uint32_t buttonChanged = 0;

bool readMpu(uint8_t address, uint8_t reg, uint8_t *data, uint8_t count) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(address, count) != count) return false;
  for (uint8_t i = 0; i < count; ++i) data[i] = Wire.read();
  return true;
}

bool writeMpu(uint8_t address, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address);
  Wire.write(reg); Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool startMpu() {
  mpuCompatible72 = false;
  const uint8_t addresses[] = {0x68, 0x69};
  for (uint8_t address : addresses) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() != 0) continue;
    uint8_t who = 0;
    if (!readMpu(address, 0x75, &who, 1)) continue;
    if (who == 0x68 && mpu.begin(address)) {
      mpuAddress = address;
      mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
      Serial.printf("INFO,MPU6050_OK,ADDRESS=0x%02X\n", address);
      return true;
    }
    // Variante observada en esta placa. No se aceptan otros IDs desconocidos.
    if (who == 0x72) {
      uint8_t again = 0;
      bool stable = true;
      for (uint8_t i = 0; i < 3; ++i)
        stable &= readMpu(address, 0x75, &again, 1) && again == 0x72;
      if (!stable || !writeMpu(address, 0x6B, 0x01)) continue;
      delay(100);
      if (!writeMpu(address, 0x6C, 0x00) || !writeMpu(address, 0x1A, 0x03) ||
          !writeMpu(address, 0x19, 0x09) || !writeMpu(address, 0x1C, 0x08)) continue;
      uint8_t config = 0, power = 0;
      if (!readMpu(address, 0x1C, &config, 1) || config != 0x08 ||
          !readMpu(address, 0x6B, &power, 1) || (power & 0x40)) continue;
      mpuAddress = address;
      mpuCompatible72 = true;
      Serial.printf("INFO,MPU_COMPATIBLE_72,ADDRESS=0x%02X,RANGE=4G\n", address);
      return true;
    }
    Serial.printf("ERROR,MPU_ID_NO_ADMITIDO,ADDRESS=0x%02X,WHO=0x%02X\n", address, who);
  }
  Serial.printf("ERROR,MPU6050_SIN_RESPUESTA,SDA21=%d,SCL22=%d,BUTTON27=%d\n",
                digitalRead(21), digitalRead(22), digitalRead(BUTTON_PIN));
  return false;
}

void reportI2c() {
  uint8_t found = 0;
  for (uint8_t address = 8; address < 120; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() != 0) continue;
    ++found;
    Serial.printf("INFO,I2C,ADDRESS=0x%02X", address);
    if (address == 0x68 || address == 0x69) {
      Wire.beginTransmission(address);
      Wire.write(0x75); // WHO_AM_I del MPU6050.
      if (Wire.endTransmission(false) == 0 && Wire.requestFrom(address, uint8_t(1)) == 1)
        Serial.printf(",WHO_AM_I=0x%02X", Wire.read());
    }
    Serial.println();
  }
  Serial.printf("INFO,I2C,DEVICES=%u\n", found);
}

void startTemperature() {
  thermometer.begin();
  temperatureReady = thermometer.getAddress(temperatureAddress, 0);
  if (temperatureReady) {
    thermometer.setResolution(temperatureAddress, 12);
    thermometer.setWaitForConversion(false);
    thermometer.requestTemperatures();
  }
  conversionStarted = millis();
}

float distanceCm() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  return duration ? duration * 0.0343f / 2.0f : -1.0f;
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(TRIG_PIN, LOW);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  Wire.setTimeOut(50);
  reportI2c();
  startTemperature();
  mpuReady = startMpu();
  Serial.println(mpuReady ? "INFO,MPU6050_OK" : "ERROR,MPU6050_NO_DETECTADO");
  Serial.println("INFO,READY,DATA1,temp_C,distance_cm,ax_m_s2,ay_m_s2,az_m_s2,button");
}

void loop() {
  uint32_t now = millis();
  bool raw = digitalRead(BUTTON_PIN) == LOW;
  if (raw != lastRawButton) { lastRawButton = raw; buttonChanged = now; }
  if (now - buttonChanged >= 30 && buttonPressed != raw) {
    buttonPressed = raw;
    Serial.printf("BUTTON,%d\n", buttonPressed ? 1 : 0);
  }
  if (now - conversionStarted < 1000) { delay(1); return; }

  float temperature = INVALID;
  if (temperatureReady) {
    float value = thermometer.getTempC(temperatureAddress);
    if (value != DEVICE_DISCONNECTED_C && isfinite(value)) temperature = value;
  }
  if (temperature == INVALID) startTemperature();
  else { thermometer.requestTemperatures(); conversionStarted = millis(); }

  if (!mpuReady && now - lastMpuRetry >= 5000) {
    lastMpuRetry = now;
    mpuReady = startMpu();
  }
  float ax = INVALID, ay = INVALID, az = INVALID;
  // Probe on every sample so a disconnected device is never reported as zero.
  Wire.beginTransmission(mpuAddress);
  bool present = Wire.endTransmission() == 0;
  if (mpuReady && present) {
    if (mpuCompatible72) {
      uint8_t bytes[6];
      if (readMpu(mpuAddress, 0x3B, bytes, 6)) {
        constexpr float scale = 9.80665f / 8192.0f;
        ax = int16_t((uint16_t(bytes[0]) << 8) | bytes[1]) * scale;
        ay = int16_t((uint16_t(bytes[2]) << 8) | bytes[3]) * scale;
        az = int16_t((uint16_t(bytes[4]) << 8) | bytes[5]) * scale;
      } else mpuReady = false;
    } else {
      sensors_event_t a, g, t;
      if (mpu.getEvent(&a, &g, &t)) {
        ax = a.acceleration.x; ay = a.acceleration.y; az = a.acceleration.z;
      }
    }
  } else mpuReady = false;
  Serial.printf("DATA1,%.2f,%.2f,%.3f,%.3f,%.3f,%d\n",
                temperature, distanceCm(), ax, ay, az, buttonPressed ? 1 : 0);
}
