# Adaptación actual: solo resistencias de 2 kΩ

**Conserva los 21 cables, los GPIO y el firmware.** Cambia únicamente las resistencias con USB desconectado. Necesitas cinco resistencias de 2 kΩ (2000 Ω), preferiblemente con tolerancia del 5 % o mejor.

## Protoboard pequeña: sustituir R1 de 1 kΩ

Retira la resistencia original R1, si la instalaste. Coloca:

| Resistencia física | Valor | Primera pata | Segunda pata |
|---|---|---|---|
| R1a | 2 kΩ | P:E5 | P:E10 |
| R1b | 2 kΩ | P:C5 | P:C10 |
| R2 | 2 kΩ | P:D10 | P:D2 |

R1a y R1b quedan **en paralelo** porque C5 y E5 están unidos por la protoboard y C10 y E10 también. Su equivalente es 1 kΩ. R2 se conserva donde estaba: D10–D2.

Los cables 16 (A5, desde ECHO), 18 (B10, hacia D19), 17 (A2, GND) y 19 (C2, tierra del pulsador) permanecen en sus posiciones. No ocupes dos veces un agujero ni añadas puentes entre las filas 5 y 10.

```text
Fila 5, A–E (ECHO) ─┬─ [R1a 2 kΩ] ─┬─ Fila 10, A–E → D19
                    └─ [R1b 2 kΩ] ─┘          │
                                          [R2 2 kΩ]
                                              │
                                          Fila 2 → GND
```

Se mantiene el divisor original: 5 × 2/(1 + 2) ≈ **3,33 V**. No sustituyas R1 por una sola de 2 kΩ manteniendo R2 en 2 kΩ: obtendrías 2,5 V, demasiado cerca del mínimo de nivel alto del ESP32 para una conexión robusta. La simulación digital no comprueba por sí sola ese margen eléctrico.

## Protoboard grande: sustituir R3 de 4,7 kΩ

Retira la resistencia original R3, si la instalaste. Coloca:

| Resistencia física | Valor | Primera pata | Segunda pata |
|---|---|---|---|
| R3a | 2 kΩ | G:E1 | G:E8 |
| R3b | 2 kΩ | G:D8 | G:E15 |

E8 y D8 están unidos internamente: forman el punto intermedio de dos resistencias **en serie**, de 4 kΩ en total. Mantén libre el resto de ese grupo G8. Se cuentan los grupos desde el primer agujero izquierdo, como en el plano anterior de la grande.

```text
G1: 3,3 V → R3a 2 kΩ → G8 → R3b 2 kΩ → G15: DAT
```

Los cables 01, 04 y 07 permanecen en A1/B1/C1, y los 06 y 21 en A15/B15. El sensor sigue a 3,3 V. Un pull-up de 4 kΩ es adecuado para este bus corto de un sensor con alimentación de tres hilos; no cambia la precisión de temperatura ni requiere cambiar código. Si el adaptador incorpora además un pull-up de 4,7 kΩ, el equivalente será aproximadamente 2,16 kΩ; a 3,3 V la corriente de nivel bajo queda dentro de la capacidad indicada para el DS18B20.

No es necesario retirar componentes SMD del adaptador. La opción predeterminada usa las cinco resistencias externas para evitar depender de una resistencia interna aún no medida. Si has confirmado con multímetro que el adaptador tiene 4,7 kΩ entre DAT y VCC, puedes omitir R3a/R3b y utilizar solo las tres resistencias de la pequeña.

## Comprobación

1. Desconecta USB y retira las resistencias antiguas que estás sustituyendo; R2 de 2 kΩ se mantiene.
2. Instala las cinco resistencias de la tabla. No cambies el resto del cableado.
3. Revisa especialmente que C5–C10 y E5–E10 sean dos resistencias en paralelo, y que D10–D2 vaya a GND.
4. Antes de alimentar, comprueba las posiciones y que ninguna pata desnuda toque otra conexión. La simulación verifica firmware y conexiones lógicas, pero no sustituye medir las resistencias del montaje real.

[Plano actualizado](04-resistencias-2k.png) · [Guía de los 21 cables, que se mantienen](index.html)

Referencias: [características eléctricas ESP32, tabla 5-3](https://documentation.espressif.com/esp32_datasheet_en.html), [DS18B20, características eléctricas y bus 1-Wire](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf).
