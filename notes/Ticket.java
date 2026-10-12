import java.util.Scanner;

public class Ticket{
	public static void main(String [] args){
		
		Scanner scanner = new Scanner(System.in);
		
		System.out.println("Welcome to SM Cinema!");
		System.out.print("\nEnter your age: ");
		
		int age = scanner.nextInt();
		String parents;
		
		if(age < 0){
			System.out.println("Invalid input");
			return;	
		} 
		//13 below
		else if (age < 13){
			System.out.print("Are you with you parents?(Yes/No): ");
			parents = scanner.next();
			if(parents.equalsIgnoreCase("No")){
				System.out.println("You can only watch: G");
			}else if (parents.equalsIgnoreCase("Yes")){
				System.out.println("You can watch: G, PG");
			} else{
				System.out.print("Invalid input...");
				return;
			}
		}
		//below 16
		else if(age < 16){
			System.out.print("Are you with your parents?(Yes/No): ");
			parents = scanner.next();
			if(parents.equalsIgnoreCase("No")){
				System.out.println("You can watch: G, PG");
			} else if (parents.equalsIgnoreCase("Yes")){
				System.out.println("You can watch: G, PG, R");
			} else{
				System.out.println("Invalid Input...");
				return;
			}
		} 
		//16 and above
		else {
			System.out.println("You can watch: G, PG, R");
		}
		
		int money;
		
		System.out.println("3D = 500$");
		System.out.println("2D = 300$");
		System.out.print("How much money do you have?: ");
		money = scanner.nextInt();
		
		if(money < 0){
			System.out.println("Invalid Input...");
			return;
		} else if (money < 300){
			System.out.println("Insufficient Funds");
			return;
		} 	
		System.out.println("You have: " + money + "$");
		
		int price;
		int howMany;
		int total;

		System.out.print("What type of movie are you watching?(3D/2D): ");
		String movieType = scanner.next();
		
		if(movieType.equalsIgnoreCase("3D")){
			price = 500;
			if(money < 500){
				System.out.println("Insufficient funds...");
				return;
			}
		} else if (movieType.equalsIgnoreCase("2D")){
			price = 300;
		} else {
			System.out.println("Invalid Input...");
			return;
		}
		System.out.print("How many are you watching?: ");
		howMany = scanner.nextInt();
		
		total = price * howMany;
		
		if(howMany <= 0){
			System.out.println("Invalid input...");
			return;
		} else if(total > money){
			System.out.println("Insufficient Funds...");
			return;
		} 
		System.out.println("Your total is: " + total + "$");
		
		int change;
		
		change = money - total;
		System.out.println("Here is your change: " + change + "$");
		System.out.println("Enjoy your movie!");
		
		
		
	}
}