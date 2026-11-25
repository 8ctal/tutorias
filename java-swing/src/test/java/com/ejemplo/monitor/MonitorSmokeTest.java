package com.ejemplo.monitor;

import javax.swing.*;
import java.lang.reflect.*;

/** Verifica el protocolo compartido con firmware, incluidos errores de sensores. */
public class MonitorSmokeTest {
    static MonitorSensoresApp app;
    static void expect(String field, String expected) throws Exception {
        Field f = MonitorSensoresApp.class.getDeclaredField(field);
        f.setAccessible(true);
        String actual = ((JLabel) f.get(app)).getText();
        if (!expected.equals(actual)) throw new AssertionError(field + ": " + actual + " != " + expected);
    }
    static void feed(String line) throws Exception {
        Method method = MonitorSensoresApp.class.getDeclaredMethod("processLine", String.class);
        method.setAccessible(true);
        SwingUtilities.invokeAndWait(() -> {
            try { method.invoke(app, line); } catch (Exception e) { throw new RuntimeException(e); }
        });
        SwingUtilities.invokeAndWait(() -> {});
    }
    public static void main(String[] args) throws Exception {
        try {
            SwingUtilities.invokeAndWait(() -> app = new MonitorSensoresApp());
            if (args.length > 0 && args[0].equals("--wokwi")) {
                Method connect = MonitorSensoresApp.class.getDeclaredMethod("connectSimulation");
                connect.setAccessible(true);
                SwingUtilities.invokeAndWait(() -> {
                    try { connect.invoke(app); } catch (Exception e) { throw new RuntimeException(e); }
                });
                long deadline = System.currentTimeMillis() + 20000;
                boolean[] received = {false};
                while (System.currentTimeMillis() < deadline && !received[0]) {
                    Thread.sleep(200);
                    SwingUtilities.invokeAndWait(() -> {
                        try {
                            expect("temperatureValue", "22.00 °C");
                            expect("distanceValue", "75.63 cm");
                            expect("axValue", "0.00");
                            expect("ayValue", "0.00");
                            expect("azValue", "9.81");
                            expect("buttonValue", "LIBRE");
                            received[0] = true;
                        } catch (Exception | AssertionError ignored) { }
                    });
                }
                if (!received[0]) throw new AssertionError("No llegaron las lecturas de Wokwi a Swing");
                System.out.println("PASS: Wokwi -> RFC2217 -> Python -> TCP -> etiquetas Swing.");
                return;
            }
            feed("DATA1,22.50,75.25,1.250,2.500,9.807,1");
            SwingUtilities.invokeAndWait(() -> {
                try {
                    expect("temperatureValue", "22.50 °C");
                    expect("distanceValue", "75.25 cm");
                    expect("axValue", "1.25");
                    expect("ayValue", "2.50");
                    expect("azValue", "9.81");
                    expect("buttonValue", "PULSADO");
                } catch (Exception e) { throw new RuntimeException(e); }
            });
            feed("DATA1,-9999,-1,-9999,-9999,-9999,0");
            feed("INFO,READY");
            feed("DATA1,bad,75,1,2,3,1");
            feed("BUTTON,1");
            SwingUtilities.invokeAndWait(() -> {
                try { expect("buttonValue", "PULSADO"); } catch (Exception e) { throw new RuntimeException(e); }
            });
            feed("BUTTON,0");
            SwingUtilities.invokeAndWait(() -> {
                try {
                    expect("temperatureValue", "--");
                    expect("distanceValue", "Sin eco");
                    expect("axValue", "--");
                    expect("buttonValue", "LIBRE");
                } catch (Exception e) { throw new RuntimeException(e); }
            });
            System.out.println("PASS: protocolo DATA1, ejes independientes, sensores ausentes y líneas inválidas.");
        } finally {
            if (app != null) SwingUtilities.invokeAndWait(() -> {
                try {
                    Method disconnect = MonitorSensoresApp.class.getDeclaredMethod("disconnect");
                    disconnect.setAccessible(true);
                    disconnect.invoke(app);
                } catch (Exception e) { throw new RuntimeException(e); }
                finally { app.dispose(); }
            });
        }
    }
}
