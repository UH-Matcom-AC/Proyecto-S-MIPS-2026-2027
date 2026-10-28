import com.cburch.logisim.prefs.AppPreferences;
import com.cburch.logisim.proj.Projects;
import java.nio.file.Files;
import java.nio.file.Path;

/** Abre el circuito en Logisim; si tiene entidades VHDL, configura Questa y activa la simulacion VHDL. */
class OpenCircuit {
  public static void main(String[] args) throws Exception {
    var bin = Path.of(args[1]);
    boolean vhdl = Files.readString(Path.of(args[0])).contains("<vhdl ");
    if (vhdl && !Files.isDirectory(bin)) throw new IllegalArgumentException("El circuito tiene VHDL y no existe la carpeta de Questa: " + bin);
    if (Files.isDirectory(bin)) AppPreferences.QUESTA_PATH.set(bin.toString());
    AppPreferences.QUESTA_VALIDATION.set(false);
    AppPreferences.VHDL_STANDARD.set(AppPreferences.VHDL_STANDARD_2002);
    com.cburch.logisim.Main.main(new String[] {args[0]});
    if (!vhdl) return;  // sin entidades VHDL no hace falta Questa
    // Main abre la ventana de forma asincrona: se espera al proyecto y se arranca Questa.
    for (int i = 0; i < 600 && Projects.getOpenProjects().isEmpty(); i++) Thread.sleep(100);
    for (var project : Projects.getOpenProjects()) project.getVhdlSimulator().enable();
  }
}
