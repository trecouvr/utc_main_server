#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include "message.h"



///
/// Envoie un int
///
inline void send(const int id_msg, const int i)
{
    cout <<id_msg << C_SEP_SEND << i << endl;
    cout.flush();
}

///
/// Envoie un str
///
inline void send(const int id_msg, const string s)
{
    cout <<id_msg << C_SEP_SEND << s << endl;
    cout.flush();
}

///
/// Envoie un vecteur
///
template <typename T>
inline void send(const int id_msg, const vector<T> &v)
{
    cout << id_msg; // send id of msg
    // send the type and location of pieces
    for (int i=0;i<v.size(); ++i)
    {
        cout << C_SEP_SEND << v[i];
    }
    cout << endl;
    cout.flush();
}


inline void split(const string &str, vector<int> &v, const string &delimiters, const string::size_type &begin=0)
{
    // clear vector
    v.clear();
    // Skip delimiters at beginning.
    string::size_type lastPos = str.find_first_not_of(delimiters, begin);
    // Find first "non-delimiter".
    string::size_type pos     = str.find_first_of(delimiters, lastPos);

    while (string::npos != pos || string::npos != lastPos)
    {
        // Found a token, add it to the vector.
        v.push_back(atoi(str.substr(lastPos, pos - lastPos).c_str()));
        // Skip delimiters.  Note the "not_of"
        lastPos = str.find_first_not_of(delimiters, pos);
        // Find next "non-delimiter"
        pos = str.find_first_of(delimiters, lastPos);
    }
}


inline void readIncomingData(vector<int> &v)
{
    string msg;
    // read message
    cin >> msg;
    // split it and put it in v
    string delimiters = "";
    delimiters += C_SEP_SEND;
    split(msg,v,delimiters);
}


