# Montaje real, cable por cable

Preparado con tus fotos de `images/` y los GPIO del firmware que pasó la simulación.

## Cómo colocar las piezas

- **ESP32 fuera de las protoboards**, sobre una superficie aislante. La orientación del dibujo coincide con tu foto: antena a la izquierda, conector USB a la derecha. Los nombres se leen en la serigrafía; D21 significa GPIO21. Usa el GND de la misma hilera que VIN, inmediatamente a su lado.
- **Grande (G)** horizontal, A arriba y J abajo, como en la foto. Solo usamos su bloque A–E. Para evitar ambigüedad de los números impresos, los grupos **G1, G2… se cuentan desde el primer agujero del extremo izquierdo**. `G:A5` es el quinto agujero de la línea A contado desde la izquierda, no necesariamente el número impreso 5. A–E del mismo grupo están conectados internamente.
- **Pequeña (P)** vertical, como en tu foto, A–J arriba, fila 1 arriba. Aquí **sí usamos los números y letras impresos**. `P:E10` significa E10. A–E de una fila están unidos; F–J de esa fila forman otro grupo separado.
- TZT, MPU y HC-SR04 quedan fuera de la rejilla y se conectan con cables a sus pines macho. Esto deja libres sus etiquetas y evita asumir una separación mecánica de pines.
- Retira el pulsador que aparece suelto en la grande. Solo se insertará en la pequeña después de comprobar sus contactos, como se explica abajo. Los carriles laterales +/− quedan sin usar: no dependemos de sus cortes internos.

## Diagramas

1. [Conexiones y pines del ESP32](01-conexiones.svg)
2. [Cada agujero de la protoboard grande](02-protoboard-grande.svg)
3. [Divisor y pulsador en la protoboard pequeña](03-protoboard-pequena.svg)

Los IDs **01–21** del dibujo corresponden a la tabla. Los colores son una recomendación para los cables nuevos; los nombres de los terminales mandan sobre el color.

Los planos muestran las conexiones y la posición de cada contacto; no son plantillas a escala 1:1 para perforar o cortar cables.

## Antes de conectar USB

Necesitas **15 cables hembra–macho, 3 hembra–hembra y 3 macho–macho**, más **cinco resistencias de 2 kΩ**. R1a y R1b forman 1 kΩ en paralelo; R3a y R3b forman 4 kΩ en serie. H = extremo hembra que recibe un pin del módulo; M = extremo macho para un agujero. No uses cables pelados apoyados sobre los pines del ESP32.

La sonda se conecta al borne verde del TZT según tu confirmación: **amarillo → DAT, rojo → VCC y negro → GND**. Conecta después los pines macho DAT/VCC/GND del adaptador según la tabla. El adaptador se alimenta con **3,3 V**. No conectes otra fuente externa junto con USB.

El montaje incluye R3a y R3b en serie para garantizar un pull-up externo de 4 kΩ. El adaptador parece tener una resistencia SMD de 4,7 kΩ: si se confirma entre DAT y VCC, puedes omitir ambas resistencias externas. Si mantienes el pull-up interno de 4,7 kΩ y el externo de 4 kΩ, el equivalente es aproximadamente 2,16 kΩ, admisible para este bus corto a 3,3 V. No retires componentes SMD. [Detalle de la adaptación](SOLO-2K.md).

## Los 21 cables

| ID | Extremo 1 | Extremo 2 | Color sugerido | Terminales |
|---|---|---|---|---|
| 01 | `ESP:3V3` | `G:A1` | fucsia (3,3 V) | H–M |
| 02 | `ESP:GND` | `G:A5` | negro | H–M |
| 03 | `ESP:VIN` | `G:A10` | rojo (5 V) | H–M |
| 04 | `TZT:VCC` | `G:B1` | fucsia (3,3 V) | H–M |
| 05 | `TZT:GND` | `G:B5` | negro | H–M |
| 06 | `TZT:DAT` | `G:A15` | amarillo | H–M |
| 07 | `MPU:VCC` | `G:C1` | fucsia (3,3 V) | H–M |
| 08 | `MPU:GND` | `G:C5` | negro | H–M |
| 09 | `MPU:AD0` | `G:D5` | negro | H–M |
| 10 | `MPU:SDA` | `ESP:D21` | verde | H–H |
| 11 | `MPU:SCL` | `ESP:D22` | azul | H–H |
| 12 | `G:E5` | `G:A6` | negro | M–M |
| 13 | `HC:VCC` | `G:B10` | rojo (5 V) | H–M |
| 14 | `HC:GND` | `G:B6` | negro | H–M |
| 15 | `HC:TRIG` | `ESP:D18` | naranja | H–H |
| 16 | `HC:ECHO` | `P:A5` | morado | H–M |
| 17 | `G:C6` | `P:A2` | negro | M–M |
| 18 | `P:B10` | `ESP:D19` | cian | M–H |
| 19 | `P:C2` | `P:J20` | negro | M–M |
| 20 | `P:A20` | `ESP:D27` | violeta | M–H |
| 21 | `ESP:D4` | `G:B15` | amarillo | H–M |

`ESP` = ESP32; `TZT` = adaptador de temperatura; `MPU` = MPU-6050; `HC` = HC-SR04. El cable 12 prolonga GND de G5 a G6; el 17 lleva GND a la pequeña. No hay un cable adicional entre nodos que ya están unidos por las tiras internas de la protoboard.

## Las cinco resistencias de 2 kΩ

| Pieza | Valor | Primera pata | Segunda pata | Función |
|---|---|---|---|---|
| R1a | 2 kΩ | P:E5 | P:E10 | En paralelo con R1b |
| R1b | 2 kΩ | P:C5 | P:C10 | En paralelo con R1a: equivalente 1 kΩ |
| R2 | 2 kΩ | P:D10 | P:D2 | Del nodo de lectura a GND |
| R3a | 2 kΩ | G:E1 | G:E8 | Primer tramo del pull-up |
| R3b | 2 kΩ | G:D8 | G:E15 | En serie con R3a: equivalente 4 kΩ |

Las resistencias no tienen polaridad. Aísla las patas desnudas que puedan tocar otras conexiones. Los únicos contactos eléctricos de cada resistencia son sus dos extremos indicados. G:D8 y G:E8 están unidos internamente y forman el punto intermedio del pull-up; el resto de G8 queda libre.

Con resistencias de cuatro bandas: 2 kΩ = rojo/negro/rojo, más su banda de tolerancia. Confirma el valor con multímetro si el código de bandas es distinto. Usa tolerancia del 5 % o mejor.

El recorrido de ECHO es:

```text
HC ECHO ── cable 16 ── P:A5 [misma tira que E5]
                                 │
                       R1a 2 kΩ ∥ R1b 2 kΩ
                                 │
P:B10 ── cable 18 ── ESP D19 ── nodo de la fila 10, A–E
                                 │
                              R2 2 kΩ
                                 │
                         fila 2, A–E ── GND
```

R1a entra en E10, R1b en C10 y R2 en D10: comparten el nodo de la fila 10 a través de la protoboard, sin ocupar el mismo agujero. Con 5 V en ECHO, el divisor entrega aproximadamente 3,33 V a D19. **No conectes ECHO directamente a D19 y no puentes R1a/R1b.**

## Pulsador: posición y comprobación necesaria

La foto muestra un pulsador de cuatro patas, pero no permite comprobar cuáles están unidas internamente. Por eso esta colocación depende de una comprobación real, no de deducirlo por el plástico.

1. Sin USB ni otra alimentación, verifica con multímetro dos pares que estén unidos permanentemente. Entre un par y el otro debe haber continuidad únicamente al pulsar.
2. Colócalo cruzando el canal central de la pequeña, con patas en **E20, F20, E22 y F22**, si encaja sin doblarlas a la fuerza. Debe cumplirse: E20–E22 unidos siempre; F20–F22 unidos siempre; E20–F20 unidos solo al pulsar. Si no coincide, identifica los pares y cambia la orientación; no alimentes hasta que coincida.
3. El cable **20** entra en **A20** y va a **ESP D27**. El **19** entra en **J20** y viene de **P:C2 (GND)**. El firmware ya usa `INPUT_PULLUP`; no necesita resistencia externa en el pulsador.
4. Si no encaja mecánicamente, deja el pulsador fuera y usa cables a un contacto de cada par: uno a A20 y otro a J20. El circuito eléctrico es el mismo.

En el MPU quedan **XDA, XCL e INT libres**. AD0 sí va a GND para usar la dirección I²C 0x68. No se conectan otros pines del ESP32.

## Orden de montaje y primera alimentación

1. Mantén USB desconectado. Coloca R1a, R1b, R2, R3a y R3b. Las cinco son de 2 kΩ. Comprueba sus valores.
2. Conecta los cables 01–05, 07–09, 12–14 y 17 (alimentación y tierras). Verifica que G1, G5/G6 y G10 estén separados: 3,3 V, GND y 5 V respectivamente.
3. Conecta los cables 06, 10, 11, 15, 16, 18 y 21 (señales).
4. Comprueba los contactos del pulsador, colócalo y conecta 19 y 20.
5. Revisa la sonda: DAT/amarillo, VCC/rojo, GND/negro, según tu confirmación. Comprueba que los tornillos sujeten el conductor y que no haya hilos sueltos.
6. Sin alimentación, comprueba que no exista un cortocircuito permanente entre alimentación y GND. Comprueba las uniones de las protoboards y el divisor según el dibujo.
7. Conecta únicamente USB al ESP32. Mide aproximadamente 3,3 V entre G1 y G5/G6 y 5 V entre G10 y G5/G6. Si VIN no entrega aproximadamente 5 V con USB, desconecta y revisa la variante de la placa antes de alimentar el HC-SR04.
8. El ESP32 aislado fue detectado en COM3 y ya se cargó el firmware. Si necesitas cargarlo otra vez: `powershell -ExecutionPolicy Bypass -File scripts/upload.ps1 -Port COM3`, comprobando antes que siga siendo ese puerto. Después abre `scripts/monitor.ps1` y conecta Java a ese COM.

Este documento define el cableado; no afirma que el montaje físico ya esté comprobado. La topología de las tiras de las protoboards y los contactos del pulsador se verifican sin alimentación. El firmware ya fue compilado y probado en Wokwi.

## Referencias

- Fotos propias: `images/ESP32.jpg`, `TZT-DS1820.jpg`, `MPU-6050-FRONT.jpg`, `MPU-6050-BACK.jpg`, `HC-SR04-FRONT.jpg` y ambas protoboards.
- [DS18B20: alimentación, pull-up y niveles de bus](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf).
- [ESP32: características eléctricas y GPIO](https://documentation.espressif.com/esp32_datasheet_en.html).
- [HC-SR04: VCC, TRIG, ECHO y GND](https://docs.wokwi.com/parts/wokwi-hc-sr04).
