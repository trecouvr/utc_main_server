#ifndef MESSAGE_H_
#define MESSAGE_H_

#include "protocole.h"

using namespace std;

void readIncomingData(vector<int> & v);
inline void send(const int id_msg, const int i);
inline void send(const int id_msg, const string s);
template <typename T>
inline void send(const int id_msg, const vector<T> &v);

#endif /* MESSAGE_H_ */

