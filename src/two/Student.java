package two;

public class Student extends Person {
    private int studentGrade;

    public Student(String firstName, String lastName, boolean isActive, int studentGrade) {
        super(firstName, lastName, isActive);
        this.studentGrade = studentGrade;
    }

    public int getStudentGrade() {
        return studentGrade;
    }

    public void setStudentGrade(int studentGrade) {
        this.studentGrade = studentGrade;
    }

    @Override
    public void showInfo() {
        super.showInfo();
        System.out.println(getStudentGrade());
    }
}
