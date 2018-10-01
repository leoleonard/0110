package two;

public class Person {
    private String firstName;
    private String lastName;
    private boolean isActive;

    public Person(String firstName, String lastName, boolean isActive) {
        this.firstName = firstName;
        this.lastName = lastName;
        this.isActive = isActive;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public boolean isActive() {
        return isActive;
    }

    public boolean getIsActive() {
        return isActive;
    }


    public void showInfo() {
        System.out.println(getFirstName() + " " + getLastName() + " " + getIsActive() + " ");
    }

}
