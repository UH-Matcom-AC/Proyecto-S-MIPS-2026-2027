import com.cburch.logisim.file.Loader;
import com.cburch.logisim.instance.Instance;
import com.cburch.logisim.instance.StdAttr;
import java.io.File;

/** Vuelca, por circuito, la posicion de cada puerto de cada componente (no cables). */
class Ports {
  public static void main(String[] args) {
    try { volcar(args[0]); } catch (Throwable e) { e.printStackTrace(); System.exit(1); }
    System.exit(0);
  }
  static void volcar(String path) throws Exception {
    var file = new Loader(null).openLogisimFile(new File(path));
    file.stopAutosaveThread(false);
    for (var circuit : file.getCircuits())
      for (var c : circuit.getNonWires()) {
        var instance = Instance.getInstanceFor(c);
        var b = c.getBounds();
        for (int i = 0; i < c.getEnds().size(); i++) {
          var end = c.getEnd(i);
          String label = c.getAttributeSet().containsAttribute(StdAttr.LABEL) ? c.getAttributeSet().getValue(StdAttr.LABEL) : "";
          String tip = c.getFactory().getName().equals("Pin") ? label : instance != null && i < instance.getPorts().size() && instance.getPorts().get(i).getToolTip() != null
              ? instance.getPorts().get(i).getToolTip() : "";
          System.out.println(String.join("\t", circuit.getName(), c.getFactory().getName(), c.getLocation().toString(),
              String.valueOf(i), tip, end.getLocation().getX() + "," + end.getLocation().getY(),
              String.valueOf(end.getWidth().getWidth()), String.valueOf(end.getType()),
              b.getX() + "," + b.getY() + "," + b.getWidth() + "," + b.getHeight()));
        }
      }
  }
}
