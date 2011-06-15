/*
  Petit test !
 */

#include "message.h"
#include "command.h"



void setup()
{
    initSerialLink(); // Initialisation de la lisaison serie (voir message.cpp)
}

void loop()
{
    readIncomingData();
}




