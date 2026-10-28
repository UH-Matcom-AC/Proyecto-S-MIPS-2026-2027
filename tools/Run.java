import com.cburch.logisim.circuit.*;
import com.cburch.logisim.comp.Component;
import com.cburch.logisim.data.Value;
import com.cburch.logisim.file.Loader;
import com.cburch.logisim.gui.hex.HexFile;
import com.cburch.logisim.gui.main.Frame;
import com.cburch.logisim.instance.InstanceDataSingleton;
import com.cburch.logisim.instance.StdAttr;
import com.cburch.logisim.prefs.AppPreferences;
import com.cburch.logisim.proj.Project;
import com.cburch.logisim.std.memory.Mem;
import com.cburch.logisim.std.memory.MemContents;
import java.io.File;
import java.util.*;
import javax.swing.*;

/**
 * Ejecuta programas en la placa con la CPU. Si la CPU tiene entidades VHDL, cosimula con Questa.
 * Uso: java Run.java smips.circ ciclos_max traza imagen1.hex [imagen2.hex ...]
 * Por cada imagen imprime una linea: RESULTADO<TAB>imagen<TAB>detenido<TAB>ciclos<TAB>mem_addr<TAB>tty(hex).
 * Con traza > 0 imprime MEM_ADDR, MEM_RDATA y las senales de escritura de los primeros `traza` ciclos.
 * Solo usa las senales de la placa, asi que funciona con cualquier organizacion interna de la CPU.
 */
class Run {
  static Project project; static Frame frame; static CircuitState board, memoria;
  static Component reset; static boolean vhdl;

  static Component find(CircuitState s, String kind, String label) {
    for (var c : s.getCircuit().getNonWires())
      if (c.getFactory().getName().equals(kind) && (label == null || label.equals(c.getAttributeSet().getValue(StdAttr.LABEL))))
        return c;
    throw new AssertionError(kind + " " + label + " en " + s.getCircuit().getName());
  }
  static CircuitState sub(CircuitState s, String kind) {
    var c = find(s, kind, null);
    return ((SubcircuitFactory) c.getFactory()).getSubstate(s, c);
  }
  /** Crea el estado de cada subcircuito y devuelve cuantas entidades VHDL hay en la jerarquia. */
  static int crearSubestados(CircuitState s) {
    int vhdl = 0;
    for (var c : s.getCircuit().getNonWires()) {
      if (c.getFactory() instanceof SubcircuitFactory f) vhdl += crearSubestados(f.getSubstate(s, c));
      else if (c.getFactory() instanceof com.cburch.logisim.vhdl.base.VhdlEntity) vhdl++;
    }
    return vhdl;
  }
  static long value(CircuitState s, String tunnel) {
    Value v = s.getValue(find(s, "Tunnel", tunnel).getLocation());
    return v.isFullyDefined() ? v.toLongValue() : -1;
  }
  static void settle() {
    board.getPropagator().propagate();
    if (board.getPropagator().isOscillating()) throw new AssertionError("Oscilacion");
  }
  static void cycle() { for (int i = 0; i < 2; i++) { board.getPropagator().toggleClocks(); settle(); } }
  static void pressReset(boolean pressed) {
    board.getInstanceState(reset).setData(new InstanceDataSingleton(pressed ? Value.TRUE : Value.FALSE));
    board.markComponentAsDirty(reset); settle();
  }
  static String terminal() throws Exception {
    Object data = board.getData(find(board, "TTY", null));
    if (data == null) return "";
    var row = data.getClass().getDeclaredMethod("getRowString", int.class); row.setAccessible(true);
    var cursor = data.getClass().getDeclaredMethod("getCursorRow"); cursor.setAccessible(true);
    int last = (Integer) cursor.invoke(data); var text = new StringBuilder();
    for (int i = 0; i <= last; i++) { if (i > 0) text.append('\n'); text.append(((String) row.invoke(data, i)).stripTrailing()); }
    return text.toString();
  }
  static String hex(String s) {
    var b = new StringBuilder();
    for (byte x : s.getBytes(java.nio.charset.StandardCharsets.UTF_8)) b.append(String.format("%02x", x));
    return b.toString();
  }
  static void initialize(String path) throws Exception {
    AppPreferences.QUESTA_PATH.set(System.getenv().getOrDefault("QUESTA_BIN", System.getProperty("user.home") + "/altera/25.1std/questa_fse/bin"));
    AppPreferences.QUESTA_VALIDATION.set(false);
    AppPreferences.VHDL_STANDARD.set(AppPreferences.VHDL_STANDARD_2002);
    var file = new Loader(null).openLogisimFile(new File(path)); file.stopAutosaveThread(false);
    project = new Project(file);
    project.getSimulator().setAutoPropagation(false); project.getSimulator().setAutoTicking(false);
    project.getSimulator().shutDown(); ((Thread) project.getSimulator().simThread).join(5000);
    board = CircuitState.createRootState(project, file.getCircuit("Board"), Thread.currentThread());
    project.setCircuitState(board);
    memoria = sub(board, "Memory"); reset = find(board, "Button", "Reset");
    // Logisim solo arranca los VHDL de subcircuitos cuyo estado ya existe.
    vhdl = crearSubestados(board) > 0;
    SwingUtilities.invokeAndWait(() -> { frame = new Frame(project); project.setFrame(frame); frame.setVisible(false); });
    if (vhdl) {  // sin entidades VHDL no hace falta Questa
      project.getVhdlSimulator().enable();
      long deadline = System.nanoTime() + 60_000_000_000L;
      while (!project.getVhdlSimulator().isRunning() && System.nanoTime() < deadline) Thread.sleep(50);
      if (!project.getVhdlSimulator().isRunning()) throw new AssertionError("Questa no arranco: " + consola());
      project.getVhdlSimulator().getSocketClient().getSocket().setTcpNoDelay(true);
    }
    settle();
  }
  static String consola() throws Exception {
    var f = frame.getVhdlSimulatorConsole().getClass().getDeclaredField("logContent"); f.setAccessible(true);
    return ((JTextArea) f.get(frame.getVhdlSimulatorConsole())).getText();
  }
  static void run(String image, int max, int trace) throws Exception {
    var ram = find(memoria, "RAM", null);
    MemContents contents = ((Mem) ram.getFactory()).getContents(memoria.getInstanceState(ram));
    pressReset(true); cycle();
    contents.clear(); HexFile.open(contents, new File(image)); memoria.markComponentAsDirty(ram);
    cycle(); pressReset(false);
    int cycles = 0; boolean halted = false;
    while (cycles < max) {
      if (cycles < trace)
        System.out.printf("TRAZA\t%d\tMEM_ADDR=%08x\tMEM_RDATA=%08x\tMEM_WE=%d\tTTY_WE=%d%n", cycles,
            value(board, "MEM_ADDR"), value(board, "MEM_RDATA"), value(board, "MEM_WE"), value(board, "TTY_WE"));
      cycle(); cycles++;
      if (value(board, "HALT") == 1) { halted = true; break; }
    }
    System.out.println(String.join("\t", "RESULTADO", image, String.valueOf(halted), String.valueOf(cycles),
        String.format("%08x", value(board, "MEM_ADDR")), hex(terminal())));
    System.out.flush();
  }
  public static void main(String[] args) {
    try {
      initialize(args[0]);
      int max = Integer.parseInt(args[1]), trace = Integer.parseInt(args[2]);
      for (int i = 3; i < args.length; i++) run(args[i], max, trace);
      if (vhdl) {
        String log = consola();
        if (log.contains("** Error")) System.out.println("CONSOLA_VHDL\n" + log);
        project.getVhdlSimulator().disable();
      }
      System.exit(0);
    } catch (Throwable e) {
      e.printStackTrace();
      try { System.err.println(consola()); } catch (Throwable ignored) {}
      System.exit(2);
    }
  }
}
