#if defined(__AVR_ATmega32U4__) || defined(ARDUINO_SAMD_ZERO)
#pragma message "This is ATmega32U4 or SAMD_ZERO"
#define SerialDevice SerialUSB
#define PN532_SPI_SS 10

#elif defined(ARDUINO_ESP8266_NODEMCU_ESP12E)
#pragma message "This is NODEMCU_ESP12E"
#define SerialDevice Serial

#elif defined(ARDUINO_NodeMCU_32S)
#define SerialDevice Serial
#define PN532_SPI_SS 5

#else
#error "Undefined board. Should check again"
#endif

#include <SPI.h>
#include <PN532_SPI.h>
PN532_SPI pn532(SPI, PN532_SPI_SS);
#include "PN532.h"
PN532 nfc(pn532);

typedef union {
  uint8_t block[18];
  struct {
    uint8_t IDm[8];
    uint8_t PMm[8];
    union {
      uint16_t SystemCode;
      uint8_t System_Code[2];
    };
  };
} Card;
Card card;

uint8_t AimeKey[6] = {0x57, 0x43, 0x43, 0x46, 0x76, 0x32};
uint8_t BanaKey[6] = {0x60, 0x90, 0xD0, 0x06, 0x32, 0xF5};
uint8_t MifareKey[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
#define M2F_B 1
uint16_t blockList[4] = {0x8080, 0x8081, 0x8082, 0x8083};
uint16_t serviceCodeList[1] = {0x000B};
uint8_t blockData[1][16];

void setup() {
  SerialDevice.begin(115200);
  while (!SerialDevice);
  nfc.begin();
  while (!nfc.getFirmwareVersion()) {
    SerialDevice.println("Didn't find PN53x board");
    delay(500);
  }
  SerialDevice.println("START!");
  nfc.setPassiveActivationRetries(0x10);
  nfc.SAMConfig();
}

void loop() {
  uint8_t uid[4], uL;

  if (nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uL) && nfc.mifareclassic_AuthenticateBlock(uid, uL, M2F_B, 0, MifareKey)) {
    // SerialDevice.println("Default Key Mifare!");
    // if (nfc.mifareclassic_ReadDataBlock(2, card.block)) {
    //   SerialDevice.print("Fake IDm:");
    //   nfc.PrintHex(card.IDm, 8);
    //   SerialDevice.print("Fake PMm:");
    //   nfc.PrintHex(card.PMm, 8);
    // }
    // SerialDevice.print("UID Value:");
    nfc.PrintHex(uid, uL);
    delay(2000);
    return;
  }
  if (nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uL)) {
    // SerialDevice.println("Unknown key Mifare.");
    // SerialDevice.print("UID Value:");
    nfc.PrintHex(uid, uL);
    delay(2000);
    return;
  }
  
  // SerialDevice.println("Didn't find card");
  delay(500);
}
