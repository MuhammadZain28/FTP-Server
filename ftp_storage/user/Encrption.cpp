# include <iostream>
# include <string>
# include <cmath>

using namespace std;

string binary(int num);
string octa(int num);
string hexa(int num);
int binaryTodecimal(int num);
int octaTodecimal(int num);
int hexaTodecimal(string num);
int hexDigits(char num);
char decDigits(int num);
void convertToAscii(string message,int arr[],int size);
string convertToText(int Ascii[],int size);
int encrypt(int num);

int* arr;

int main()
{
    int choice;
    int decimal;
    do
    {
        cout << "  1.  Binary                   " << endl;
        cout << "  2.  Octal                    " << endl;
        cout << "  3.  Decimal                  " << endl;
        cout << "  4.  Hexadecimal              " << endl;
        cout << "  5.  Encrypt into Binary      " << endl;
        cout << "  6.  Encrypt into Octal       " << endl;
        cout << "  7.  Encrypt into Hexadecimal " << endl;
        cout << "  8.  Decrypt from Binary      " << endl;
        cout << "  9.  Decrypt from Octal       " << endl;
        cout << "  10. Decrypt from Hexadecimal " << endl;
        cout << "  0.  Exit                     " << endl;
        cout << "  Enter Choice :  ";
        cin >> choice;
        if (choice == 1)
        {
            int num;
            cout << "Enter Binary Number : ";
            cin >> num;
            decimal = binaryTodecimal(num);
            cout << "Decimal      : " << decimal << endl;
            cout << "Octal        : " << octa(decimal) << endl;
            cout << "Hexadecimal  : " << hexa(decimal) << endl;
        }
        else if (choice == 2)
        {
            int num;
            cout << "Enter Octal Number : ";
            cin >> num;
            decimal = octaTodecimal(num);
            cout << "Decimal      : " << decimal << endl;
            cout << "Binary       : " << binary(decimal) << endl;
            cout << "Hexadecimal  : " << hexa(decimal) << endl;
        }
        else if (choice == 3)
        {
            int num;
            cout << "Enter Decimal Number : ";
            cin >> num;
            cout << "Binary       : " << binaryTodecimal(num) << endl;
            cout << "Octal        : " << octaTodecimal(num) << endl;
            cout << "Hexadecimal  : " << hexa(num) << endl;
        }
        else if (choice == 4)
        {
            string num;
            cout << "Enter Hexadecimal Number : ";
            cin >> num;
            decimal = hexaTodecimal(num);
            cout << "Binary       : " << binary(decimal) << endl;
            cout << "Octal        : " << octa(decimal) << endl;
            cout << "Decimal      : " << decimal << endl;
        }
        else if (choice == 5)
        {
            string message;
            cout << "  Enter Message to Encrypt : ";
            cin >> message;
            int size = message.length();
            string encrypt[size];
            int* arr = new int[size];
            convertToAscii(message,arr,size);

            for (int i = 0; i < message.length(); i++)
            {
                encrypt[i] = binary(arr[i]);
                cout << encrypt[i] << "  ";
            }
            cout << endl << endl;
        }
        else if (choice == 6)
        {
            string message;
            cout << "  Enter Message to Encrypt : ";
            cin >> message;
            int size = message.length();
            string encrypt[size];
            int* arr = new int[size];
            convertToAscii(message,arr,size);

            for (int i = 0; i < message.length(); i++)
            {
                encrypt[i] = octa(arr[i]);
                cout << encrypt[i] << "  ";
            }
            cout << endl << endl;
        }
        else if (choice == 7)
        {
            string message;
            cout << "  Enter Message to Encrypt : ";
            cin >> message;
            int size = message.length();
            string encrypt[size];
            int* arr = new int[size];
            convertToAscii(message,arr,size);

            for (int i = 0; i < message.length(); i++)
            {
                encrypt[i] = hexa(arr[i]);
                cout << encrypt[i] << "  ";
            }
            cout << endl << endl;
        }
        else if (choice == 8)
        {
            int input;
            int size;
            cout << "Enter lenght of message : ";
            cin >> size;
            cout << "Enter Encrypted Message : ";
            int arr2[size]; 
            for (int i = 0; i < size; i++)
            {
                cin >> input;
                arr2[i] = binaryTodecimal(input);
            }
            cout << "Decrypted Message :  " << convertToText(arr2,size) << endl << endl;
        }
        else if (choice == 9)
        {
            int input;
            int size;
            cout << "Enter lenght of message : ";
            cin >> size;
            cout << "Enter Encrypted Message : ";
            int arr2[size]; 
            for (int i = 0; i < size; i++)
            {
                cin >> input;
                arr2[i] = octaTodecimal(input);
            }
            cout << "Decrypted Message :  " << convertToText(arr2,size) << endl << endl;
        }
        else if (choice == 10)
        {
            string input;
            int size;
            cout << "Enter lenght of message : ";
            cin >> size;
            cout << "Enter Encrypted Message : ";
            int arr2[size]; 
            for (int i = 0; i < size; i++)
            {
                cin >> input;
                arr2[i] = hexaTodecimal(input);
            }
            cout << "Decrypted Message :  " << convertToText(arr2,size) << endl << endl;
        }
    } 
    while (choice != 0);

}

string binary(int num)
{
    string temp;
    string res;
    while (num != 0)
    {
        temp = temp + char(num % 2 + 48);
        num = num / 2;
    }
    int size = temp.length() - 1; 
    for (int i = size; i >= 0; i--)
    {
        res += temp[i]; 
    }
    return res;
}

string octa(int num)
{
    string temp;
    string res;
    while (num != 0)
    {
        temp = temp + char(num % 8 + 48);
        num = num / 8;
    }
    int size = temp.length() - 1; 
    for (int i = size; i >= 0; i--)
    {
        res += temp[i]; 
    }
    return res;
}

string hexa(int num)
{
    string temp;
    string res;
    while (num != 0)
    {
        temp = temp + decDigits(num % 16);
        num = num / 16;
    }
    int size = temp.length() - 1; 
    for (int i = size; i >= 0; i--)
    {
        res += temp[i]; 
    }
    return res;
}

int binaryTodecimal(int num)
{
    int digit;
    int result = 0;
    for (int i = 0; num != 0; i++)
    {
        digit = num % 10;
        num = num / 10;
        result = result + digit*pow(2,i);
    }
    return result;
}

int octaTodecimal(int num)
{
    int digit;
    int result = 0;
    for (int i = 0; num != 0; i++)
    {
        digit = num % 10;
        num = num / 10;
        result = result + digit*pow(8,i);
    }
    return result;
}

int hexaTodecimal(string num)
{
    int digit;
    int result = 0;
    int size = num.length()-1;
    for (int i = 0; i <= size; i++)
    {
        digit = hexDigits(num[size-i]);
        result = result + digit*pow(16,i);
    }
    return result;
}

int hexDigits(char num)
{
    switch (num)
    {
    case 'A':
        return 10;
    
    case 'B':
        return 11;
        
    case 'C':
        return 12;
        
    case 'D':
        return 13;
        
    case 'E':
        return 14;
    
    case 'F':
        return 15;

    default:
        return int(num) - 48;
    }
}

char decDigits(int num)
{
    switch (num)
    {
    case 10:
        return 'A';
    
    case 11:
        return 'B';
        
    case 12:
        return 'C';
        
    case 13:
        return 'D';
        
    case 14:
        return 'E';
    
    case 15:
        return 'F';

    default:
        return char(num + 48);
    }
}

void convertToAscii(string message,int ascii[],int size)
{
    for (int i = 0; i < size; i++)
    {
        ascii[i] = int(message[i]);
    }
}

string convertToText(int Ascii[],int size)
{
    string text;
    for (int i = 0; i < size; i++)
    {
        text += static_cast<char>(Ascii[i]);
    }
    return text;
}