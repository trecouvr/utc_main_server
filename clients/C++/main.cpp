#include <iostream>
#include <vector>
#include <string>
#include "message.cpp"
#include "message.h"



int main()
{
	vector<int> msg;
	readIncomingData(msg);
	cout << "id : " << msg[0] << endl;
	if (msg.size() > 1)
		cout << "cmd : " << msg[1] << endl;
	else
		cout << "cmd : None" << endl;
	if (msg.size() > 2)
	{
		cout << "params : ";
		for (int i=2; i<msg.size();++i)
			cout << msg[i] << " ";
		cout << endl;
	}
	else
		cout << "params : None" << endl;

	vector<int> v;
	v.push_back(300);
	v.push_back(400);
	
	send(msg[0],v);
	send(msg[0], "coucou");
	send(msg[0], 42);
	
	return 0;
}

