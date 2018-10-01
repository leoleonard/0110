package two;

public class School {
    public static void main(String[] args) {
        Teacher teacher1 = new Teacher("Paweł", "Nowak", true, 28);

        Student student1 = new Student("Gosia", "Andrzejewicz", false, 01);
        Student student2 = new Student("Jola", "Smyczkowska", true, 05);

        teacher1.showInfo();
        student1.showInfo();
        student2.showInfo();
    }
}
