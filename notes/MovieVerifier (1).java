import java.util.Scanner;

public class MovieVerifier {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        
        System.out.println("|====AGE===================MOVIES===|");
        System.out.println("|=UNDER 13=================G========|");
        System.out.println("|=UNDER 13 w/Parent========G,P======|");
        System.out.println("|=OVER 13 UNDER=16=========G,P======|");
        System.out.println("|=UNDER 16 w/Parent========G,P,R====|");
        System.out.println("|=16 AND OVER==============G,P,R====|");
        System.out.println("|===================================|");
        System.out.println("|===PRICE===========================|");
        System.out.println("|===P500===================3D=======|");
        System.out.println("|===P300===================2D=======|");
        System.out.println("|===================================|");
        
        System.out.print("\nEnter Your AGE: ");
        int age = scanner.nextInt();
        String parent = "no";
        
        if (age < 16) {
            System.out.print("Do you have a Parent with you? yes/no: ");
            parent = scanner.next();
        }
        
        String allowedMovies = "";
        if (age < 13) {
            if (parent.equalsIgnoreCase("yes")) {
                allowedMovies = "G, PG";
            } else {
                allowedMovies = "G";
            }
        } else if (age >= 13 && age < 16) {
             if (parent.equalsIgnoreCase("yes")) {
                allowedMovies = "G, PG, R";
            } else {
                allowedMovies = "G, PG";
            }
        } else {
            allowedMovies = "G, PG, R";
        }
        
        System.out.println("\n--> You are allowed to watch movies rated: " + allowedMovies);
        
        System.out.print("\nEnter your amount of money: P");
        int money = scanner.nextInt();
        
        if (money < 300) {
            System.out.println("Sorry, you do not have enough money to buy any ticket.");
        } else {
            System.out.print("Which ticket do you want to buy? (2D/3D): ");
            String ticket = scanner.next();
            
            if (ticket.equalsIgnoreCase("3D")) {
                if (money >= 500) {
                    int change = money - 500;
                    System.out.println("Ticket Purchased: 3D");
                    if (change > 0) {
                        System.out.println("Your change is: P" + change);
                    } else {
                        System.out.println("Exact amount received. No change.");
                    }
                } else {
                    System.out.println("Insufficient money for a 3D ticket. You only have P" + money + " but need P500.");
                }
            } else if (ticket.equalsIgnoreCase("2D")) {
                int change = money - 300;
                System.out.println("Ticket Purchased: 2D");
                if (change > 0) {
                    System.out.println("Your change is: P" + change);
                } else {
                    System.out.println("Exact amount received. No change.");
                }
            } else {
                System.out.println("Invalid ticket choice. Please type 2D or 3D.");
            }
        }
        
        scanner.close();
    }
}