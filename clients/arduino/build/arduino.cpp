#include <WProgram.h>

int main(void)
{
	init();

	setup();
    
	for (;;)
		loop();
        
	return 0;
}

#line 1 "build/arduino.pde"
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




