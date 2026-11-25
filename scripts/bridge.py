"""Puente Wokwi RFC2217 -> TCP para los monitores. Solo escucha en la máquina local."""
import select
import socket
import serial

with socket.socket() as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 4001))
    server.listen(1)
    print('Puente listo en localhost:4001. Pulsa Wokwi en Swing o en el dashboard.', flush=True)
    while True:
        client, _ = server.accept()
        try:
            with client, serial.serial_for_url('rfc2217://localhost:4000', baudrate=115200, timeout=1) as uart:
                while True:
                    if select.select([client], [], [], 0)[0] and not client.recv(1):
                        break
                    line = uart.readline()
                    if line:
                        client.sendall(line)
        except (OSError, serial.SerialException) as exc:
            print(f'Conexión cerrada: {exc}', flush=True)
