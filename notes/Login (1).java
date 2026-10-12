// FABRIGAR, ALDREI O 
import java.util.Scanner;

public class Login {
    public static void main(String[] args) {
        
        System.out.println("========NAYRE PORTAL========");
        
        Scanner scanner = new Scanner(System.in);
        System.out.print("Username: ");
        String user = scanner.nextLine();
        
        System.out.print("Password: ");
        String pass = scanner.nextLine();
        
        String verified = "Admin";
        String verifiedpass = "Admin";
        String verified2 = "Camayang";
        String verifiedpass2 = "Flores";
        
        double adminbalance = 10000;
        
        if (user.equals(verified)) {
            if (pass.equals(verifiedpass)) {
                System.out.println("\nLOGIN SUCCESS: ADMIN");      
            } else {        
                System.out.println("\nINVALID PASSWORD");
                return;
            }
        } else if (user.equals(verified2)) {
            if (pass.equals(verifiedpass2)) {
                System.out.println("\nLOGIN SUCCESS: REGULAR");
            } else {
                System.out.println("\nINVALID PASSWORD");
                return;
            }
        } else { 
            System.out.println("\nINVALID USERNAME");
            return;
        }
        
        System.out.println("\n====================NAYRE BANK===================");
        System.out.println("\n====================NAYRE BANK===================");
        System.out.println("\n========                               ==========");
        System.out.println("\n========      1.Deposit 2.Withdraw     ==========");
        System.out.println("\n========                               ==========");
        System.out.println("\n========        3.Check Balance        ==========");
        System.out.println("\n========                               ==========");
        System.out.println("\n========                               ==========");
        System.out.println("\n===================NAYRE BANK====================");
        System.out.println("\n===================NAYRE BANK====================");
        
        System.out.println("\nWelcome!\nEnter Your Designated Choice 1, 2, 3:");
        int choice = scanner.nextInt();
        
        if (choice == 1) {
            System.out.print("\nEnter Amount to Deposit: ");
            double deposit = scanner.nextDouble();
            if (deposit > 0) {
                adminbalance += deposit;
                System.out.println("Deposit Successful. Your new balance is: " + adminbalance);
            } else {
                System.out.println("Invalid deposit amount.");
            }
            
        } else if (choice == 2) {
            System.out.print("\nEnter Amount to Withdraw: ");
            double withdraw = scanner.nextDouble();
            if (withdraw > 0 && withdraw <= adminbalance) {
                adminbalance -= withdraw;
                System.out.println("Withdrawal Successful. Your new balance is: " + adminbalance);
            } else if (withdraw > adminbalance) {
                System.out.println("Insufficient funds.");
            } else {
                System.out.println("Invalid withdrawal amount.");
            }
            
        } else if (choice == 3) {
            System.out.println("\nYour current balance is: " + adminbalance);
            
        } else {
            System.out.println("Invalid choice. Please select 1, 2, or 3.");
        }
        
        scanner.close();
    }
}