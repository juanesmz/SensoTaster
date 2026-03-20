
const int ch0 = A0;
const int ch1 = A1;
const int ch2 = A2;
const int ch3 = A3;
const int ch4 = A4;
const int ch5 = A5;


void setup() {
  Serial.begin(115200);  // velocidad alta = mejor para streaming
}

void loop() {

  int v0 = analogRead(ch0);
  int v1 = analogRead(ch1);
  int v2 = analogRead(ch2);
  int v3 = analogRead(ch3);
  int v4 = analogRead(ch4);
  int v5 = analogRead(ch5);

  Serial.print(v0);
  Serial.print(", ");
  Serial.print(v1);
  Serial.print(", ");
  Serial.print(v2);
  Serial.print(", ");
  Serial.print(v3);
  Serial.print(", ");
  Serial.print(v4);
  Serial.print(", ");
  Serial.println(v5);

  delay(10);  // ajusta según tu frecuencia de muestreo
}