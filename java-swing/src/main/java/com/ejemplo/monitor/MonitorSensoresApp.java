package com.ejemplo.monitor;

import com.fazecast.jSerialComm.SerialPort;
import com.fazecast.jSerialComm.SerialPortDataListener;
import com.fazecast.jSerialComm.SerialPortEvent;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridLayout;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * Dashboard Swing que recibe por USB-Serial las lecturas generadas por el ESP32.
 * Protocolo esperado:
 * DATA1,tempC,distanceCm,ax_m_s2,ay_m_s2,az_m_s2,button
 */
public class MonitorSensoresApp extends JFrame {
    private final JComboBox<PortOption> portsCombo = new JComboBox<>();
    private final JButton refreshButton = new JButton("Buscar puertos");
    private final JButton connectButton = new JButton("Conectar");
    private final JButton disconnectButton = new JButton("Desconectar");
    private final JLabel connectionLabel = new JLabel("Desconectado");

    private final JLabel temperatureValue = valueLabel("-- °C");
    private final JLabel distanceValue = valueLabel("-- cm");
    private final JLabel axValue = valueLabel("-- m/s²");
    private final JLabel ayValue = valueLabel("-- m/s²");
    private final JLabel azValue = valueLabel("-- m/s²");
    private final JLabel buttonValue = valueLabel("--");
    private final JTextArea console = new JTextArea(8, 60);

    private static final int BAUD_RATE = 115200;
    private static final InetSocketAddress WOKWI_ADDRESS = new InetSocketAddress("127.0.0.1", 4001);

    // El hilo de eventos de Swing (EDT) es dueño de la conexión y de la interfaz.
    private final JButton simulationButton = new JButton("Wokwi");
    private Socket simulationSocket;
    private SerialPort activePort;
    private Object serialSession;

    public MonitorSensoresApp() {
        super("Monitor de sensores — ESP32");
        setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
        setMinimumSize(new Dimension(760, 520));
        setLocationByPlatform(true);
        buildUi();
        refreshPorts();
        setConnectionState(false, "Desconectado");

        refreshButton.addActionListener(e -> refreshPorts());
        connectButton.addActionListener(e -> connectToSelectedPort());
        disconnectButton.addActionListener(e -> disconnect());
        simulationButton.addActionListener(e -> connectSimulation());
        addWindowListener(new WindowAdapter() {
            @Override public void windowClosing(WindowEvent e) {
                disconnect();
                dispose();
            }
        });
    }

    private void buildUi() {
        JPanel root = new JPanel(new BorderLayout(12, 12));
        root.setBorder(BorderFactory.createEmptyBorder(14, 14, 14, 14));

        JPanel top = new JPanel();
        top.add(new JLabel("Puerto:"));
        portsCombo.setPreferredSize(new Dimension(250, 28));
        top.add(portsCombo);
        top.add(refreshButton);
        top.add(simulationButton);
        top.add(connectButton);
        top.add(disconnectButton);
        top.add(Box.createHorizontalStrut(8));
        top.add(connectionLabel);
        root.add(top, BorderLayout.NORTH);

        JPanel cards = new JPanel(new GridLayout(2, 4, 10, 10));
        cards.add(metricPanel("Temperatura", temperatureValue));
        cards.add(metricPanel("Sensor térmico", valueLabel("DS18x20")));
        cards.add(metricPanel("Distancia", distanceValue));
        cards.add(metricPanel("Pulsador", buttonValue));
        cards.add(metricPanel("Aceleración X", axValue));
        cards.add(metricPanel("Aceleración Y", ayValue));
        cards.add(metricPanel("Aceleración Z", azValue));
        cards.add(metricPanel("Unidad aceleración", valueLabel("m/s²")));

        console.setEditable(false);
        console.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        console.setLineWrap(true);
        console.setWrapStyleWord(true);
        JScrollPane logScroll = new JScrollPane(console);
        logScroll.setBorder(BorderFactory.createTitledBorder("Consola serie"));

        JPanel center = new JPanel(new BorderLayout(0, 12));
        center.add(cards, BorderLayout.CENTER);
        center.add(logScroll, BorderLayout.SOUTH);
        root.add(center, BorderLayout.CENTER);

        JLabel instructions = new JLabel(
                "ESP32: 115200 baudios · Para conectar por USB, cierre antes el monitor serie del IDE.");
        instructions.setHorizontalAlignment(SwingConstants.CENTER);
        root.add(instructions, BorderLayout.SOUTH);
        setContentPane(root);
    }

    private JPanel metricPanel(String title, JLabel value) {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createEtchedBorder(), BorderFactory.createEmptyBorder(12, 8, 12, 8)));
        JLabel titleLabel = new JLabel(title);
        titleLabel.setAlignmentX(CENTER_ALIGNMENT);
        titleLabel.setFont(titleLabel.getFont().deriveFont(Font.BOLD, 13f));
        value.setAlignmentX(CENTER_ALIGNMENT);
        panel.add(Box.createVerticalGlue());
        panel.add(titleLabel);
        panel.add(Box.createVerticalStrut(12));
        panel.add(value);
        panel.add(Box.createVerticalGlue());
        return panel;
    }

    private static JLabel valueLabel(String initial) {
        JLabel label = new JLabel(initial, SwingConstants.CENTER);
        label.setFont(label.getFont().deriveFont(Font.BOLD, 19f));
        return label;
    }

    private void refreshPorts() {
        PortOption selected = (PortOption) portsCombo.getSelectedItem();
        portsCombo.removeAllItems();
        for (SerialPort port : SerialPort.getCommPorts()) {
            portsCombo.addItem(new PortOption(port));
        }
        if (selected != null) {
            for (int i = 0; i < portsCombo.getItemCount(); i++) {
                if (portsCombo.getItemAt(i).name.equals(selected.name)) {
                    portsCombo.setSelectedIndex(i);
                    break;
                }
            }
        }
        appendConsole("Puertos detectados: " + portsCombo.getItemCount());
    }

    private void connectToSelectedPort() {
        if (activePort != null || simulationSocket != null) return;
        PortOption selected = (PortOption) portsCombo.getSelectedItem();
        if (selected == null) {
            appendConsole("No hay puertos serie disponibles. Conecte el ESP32 y pulse Buscar puertos.");
            return;
        }

        SerialPort port = selected.port;
        port.setComPortParameters(BAUD_RATE, 8, SerialPort.ONE_STOP_BIT, SerialPort.NO_PARITY);
        port.setComPortTimeouts(SerialPort.TIMEOUT_NONBLOCKING, 0, 0);
        if (!port.openPort()) {
            appendConsole("No se pudo abrir " + selected.name
                    + ". Compruebe que el puerto no esté abierto en Arduino IDE u otra aplicación.");
            return;
        }

        activePort = port;
        Object session = new Object();
        serialSession = session;
        setConnectionState(true, "Conectado: " + selected.name);
        appendConsole("Conectado a " + selected.name + " a " + BAUD_RATE + " baudios.");

        if (!port.addDataListener(serialListener(session))) {
            appendConsole("No se pudo iniciar la lectura de " + selected.name + ".");
            disconnect();
        }
    }

    private SerialPortDataListener serialListener(Object session) {
        return new SerialPortDataListener() {
            // Una sesión puede recibir una línea en varios eventos USB.
            private final StringBuilder partialLine = new StringBuilder();
            private boolean overflow;

            @Override public int getListeningEvents() {
                return SerialPort.LISTENING_EVENT_DATA_RECEIVED | SerialPort.LISTENING_EVENT_PORT_DISCONNECTED;
            }

            @Override public void serialEvent(SerialPortEvent event) {
                if (event.getEventType() == SerialPort.LISTENING_EVENT_PORT_DISCONNECTED) {
                    SwingUtilities.invokeLater(() -> {
                        if (serialSession == session) disconnect();
                    });
                    return;
                }
                byte[] bytes = event.getReceivedData();
                if (bytes == null) return;
                for (byte value : bytes) {
                    char character = (char) (value & 0xFF);
                    if (character == '\n') {
                        String line = partialLine.toString().trim();
                        if (!overflow && !line.isEmpty()) deliverSerialLine(session, line);
                        partialLine.setLength(0);
                        overflow = false;
                    } else if (character != '\r' && !overflow) {
                        if (partialLine.length() == 512) overflow = true;
                        else partialLine.append(character);
                    }
                }
            }
        };
    }

    private void deliverSerialLine(Object session, String line) {
        SwingUtilities.invokeLater(() -> {
            if (serialSession != session) return;
            System.out.println(line);
            processLine(line);
        });
    }

    private void connectSimulation() {
        if (activePort != null || simulationSocket != null) return;
        Socket socket = new Socket();
        simulationSocket = socket;
        setConnectionState(true, "Conectando a Wokwi…");

        Thread reader = new Thread(() -> readSimulation(socket), "wokwi-reader");
        reader.setDaemon(true);
        reader.start();
    }

    private void readSimulation(Socket socket) {
        // El hilo lector bloquea en TCP. Cada actualización verifica su sesión en el EDT.
        try (socket) {
            socket.connect(WOKWI_ADDRESS, 3000);
            SwingUtilities.invokeLater(() -> {
                if (simulationSocket == socket) setConnectionState(true, "Wokwi conectado");
            });
            BufferedReader input = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            String received;
            while ((received = input.readLine()) != null) {
                String line = received.trim();
                if (line.isEmpty()) continue;
                SwingUtilities.invokeLater(() -> {
                    if (simulationSocket == socket) processLine(line);
                });
            }
        } catch (IOException error) {
            SwingUtilities.invokeLater(() -> {
                if (simulationSocket == socket) {
                    appendConsole("Wokwi: " + error.getMessage() + ". Inicie el simulador y scripts/bridge.py.");
                }
            });
        } finally {
            SwingUtilities.invokeLater(() -> {
                if (simulationSocket == socket) disconnect();
            });
        }
    }

    /** Se ejecuta en el EDT. Cada muestra válida actualiza las seis lecturas juntas. */
    private void processLine(String line) {
        appendConsole("ESP32> " + line);
        if (line.equals("BUTTON,0") || line.equals("BUTTON,1")) {
            showButton(line.endsWith("1"));
            return;
        }

        String[] fields = line.split(",", -1);
        if (!"DATA1".equals(fields[0])) return;
        if (fields.length != 7 || !("0".equals(fields[6]) || "1".equals(fields[6]))) {
            appendConsole("Línea DATA1 inválida: " + line);
            return;
        }

        try {
            double temperature = Double.parseDouble(fields[1]);
            double distance = Double.parseDouble(fields[2]);
            double ax = Double.parseDouble(fields[3]);
            double ay = Double.parseDouble(fields[4]);
            double az = Double.parseDouble(fields[5]);

            temperatureValue.setText(formatValue(temperature, " °C"));
            distanceValue.setText(distance < 0 ? "Sin eco" : formatValue(distance, " cm"));
            axValue.setText(formatValue(ax, ""));
            ayValue.setText(formatValue(ay, ""));
            azValue.setText(formatValue(az, ""));
            showButton("1".equals(fields[6]));
        } catch (NumberFormatException error) {
            appendConsole("Línea DATA1 inválida: " + line);
        }
    }

    private void showButton(boolean pressed) {
        buttonValue.setText(pressed ? "PULSADO" : "LIBRE");
    }

    private static String formatValue(double value, String suffix) {
        if (!Double.isFinite(value) || value <= -1000) return "--";
        return String.format(Locale.US, "%.2f%s", value, suffix);
    }

    private void appendConsole(String message) {
        console.append(message + System.lineSeparator());
        var lines = console.getDocument().getDefaultRootElement();
        if (lines.getElementCount() > 500) {
            console.replaceRange("", 0, lines.getElement(100).getStartOffset());
        }
        console.setCaretPosition(console.getDocument().getLength());
    }

    private void setConnectionState(boolean busy, String status) {
        simulationButton.setEnabled(!busy);
        portsCombo.setEnabled(!busy);
        refreshButton.setEnabled(!busy);
        connectButton.setEnabled(!busy);
        disconnectButton.setEnabled(busy);
        connectionLabel.setText(status);
    }

    private void disconnect() {
        // Invalida primero la sesión para descartar lecturas que ya estaban en cola.
        Socket socket = simulationSocket;
        SerialPort port = activePort;
        simulationSocket = null;
        activePort = null;
        serialSession = null;

        if (socket != null) {
            try {
                socket.close();
            } catch (IOException error) {
                appendConsole("Error al cerrar Wokwi: " + error.getMessage());
            }
        }
        if (port != null) {
            port.removeDataListener();
            if (port.isOpen() && !port.closePort()) {
                appendConsole("No se pudo cerrar " + port.getSystemPortName() + ".");
            }
        }

        setConnectionState(false, "Desconectado");
        if (socket != null || port != null) appendConsole("Conexión cerrada.");
    }

    private static final class PortOption {
        private final SerialPort port;
        private final String name;

        private PortOption(SerialPort port) {
            this.port = port;
            this.name = port.getSystemPortName();
        }

        @Override public String toString() {
            String description = port.getDescriptivePortName();
            return name + (description == null || description.isBlank() ? "" : " — " + description);
        }
    }

    public static void main(String[] args) {
        if (args.length != 0 && (args.length != 2 || !args[0].equals("--port") || !args[1].matches("(?i)COM[0-9]+")))
            throw new IllegalArgumentException("Uso: MonitorSensoresApp [--port COM3]");
        SwingUtilities.invokeLater(() -> {
            MonitorSensoresApp app = new MonitorSensoresApp();
            app.setVisible(true);
            if (args.length == 2) {
                for (int i = 0; i < app.portsCombo.getItemCount(); i++) {
                    if (app.portsCombo.getItemAt(i).name.equalsIgnoreCase(args[1])) {
                        app.portsCombo.setSelectedIndex(i);
                        app.connectToSelectedPort();
                        return;
                    }
                }
                app.appendConsole("Puerto solicitado no disponible: " + args[1]);
            }
        });
    }
}
