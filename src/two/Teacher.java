package two;

public class Teacher extends Person {
    private int practiseYears;

    public Teacher(String firstName, String lastName, boolean isActive, int practiseYears) {
        super(firstName, lastName, isActive);
        this.practiseYears = practiseYears;
    }

    public int getPractiseYears() {
        return practiseYears;
    }

    public void setPractiseYears(int practiseYears) {
        this.practiseYears = practiseYears;
    }

    @Override
    public void showInfo() {
        super.showInfo();
        System.out.println(getPractiseYears());
    }
}
