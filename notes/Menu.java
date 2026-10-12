import java.util.Scanner;

public class Menu{
	public static void main(String [] args){
		
	Scanner scanner = new Scanner(System.in);
	
	String choice;
	int number;
	int numbers;
	int total;
	
	System.out.println("Menu");
	System.out.println("A. Addition");	
	System.out.println("B. Substraction");
	System.out.println("C. Multiplication");
	System.out.println("D. Average");
	System.out.println("E. Exit");
	
	System.out.print("\nEnter your choice: ");
	choice = scanner.next();
	
	switch(choice.toUpperCase()){
		case "A":
		System.out.print("Enter your first number: ");
		number = scanner.nextInt();
		
		System.out.print("Enter your second number: ");
		numbers = scanner.nextInt();
		
		total = number + numbers;
		
		System.out.println("Your total is: " + total);
		
		break;
		
		case "B":
		System.out.print("Enter your first number: ");
		number = scanner.nextInt();
		
		System.out.print("Enter your second number: ");
		numbers = scanner.nextInt();
		
		total = number - numbers;
		
		System.out.println("Your total is: " + total);
		
		break;
		
		case "C":
		System.out.print("Enter your first number: ");
		number = scanner.nextInt();
		
		System.out.print("Enter your second number: ");
		numbers = scanner.nextInt();
		
		total = number * numbers;
		
		System.out.println("Your total is: " + total);
		
		break;
		
		case "D":
		System.out.print("Enter your first number: ");
		number = scanner.nextInt();
		
		System.out.print("Enter your second number: ");
		numbers = scanner.nextInt();
		
		total = number / numbers;
		
		System.out.println("Your total is: " + total);
		
		break;
		
		case "E":
		System.out.println("Exiting...");
		return;
		
		default: System.out.println("Invalid Choices!");
		return;
	}
		
		
		
		
	}
}