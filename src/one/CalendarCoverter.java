package one;

public class CalendarCoverter {
    final static int Monday = 1;
    final static int Tuesday = 2;
    final static int Wednesday = 3;
    final static int Thursday = 4;
    final static int Friday = 5;
    final static int Saturday = 6;
    final static int Sunday = 7;

    static String convertDayToString(int dayNumber) {

        switch (dayNumber) {
            case 01:
                return "Monday";
            case 02:
                return "Tuesday";
            case 03:
                return "Wednesday";
            case 04:
                return "Thursday";
            case 05:
                return "Friday";
            case 06:
                return "Saturday";
            case 07:
                return "Sunday";
             default:
                 return "Does your week have more than 7 days?";
        }
    }
}
