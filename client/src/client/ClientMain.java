package client;

import java.util.Scanner;


public class ClientMain {


	public static void main(String[] args) {
		
		String host = "localhost";
		final int portNumber = 6060;
		String msg = null;
		Scanner reader = new Scanner(System.in);
		//int qtdClients = 0;
		
		if(args.length > 1) {
			host = args[1];
		}
		
		System.out.println("Criando um hosta para o ipZ'" + host + "' na porta " + portNumber);
		
		Client client = new Client(portNumber, host);

		System.out.println("Conexão estabelecida!");
		
		while (true) {

			System.out.println("Opções de requisição ao servidor (XXC):");
			msg = reader.nextLine();
			
			client.sendMessage(msg);
			System.out.println("Mensagem enviada : " + msg);
			
			if(client.ackReceive()) {
				
				if(msg.contains("10")) {
					
					client.receiverData();
		        
				}
			}

		}
		
	}

}
