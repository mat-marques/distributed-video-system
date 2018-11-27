package client;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.DataInput;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.UnsupportedEncodingException;
import java.net.Socket;
import java.util.LinkedList;

public class Client {
	
	private String fileName;
	private LinkedList<String> listFileNames;
	private String host;
	private int portNumber;
	private Socket socket;
	private PrintWriter out;
    private BufferedReader in;

	public Client(int portNumber, String host){
		this.host = host;
		this.portNumber = portNumber;
		this.fileName = "";
		try {
			this.socket = new Socket(host, portNumber);
			this.out = new PrintWriter(socket.getOutputStream(), true);
		    this.in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
		} catch (IOException e1) {
			System.out.println("Erro na Conexão!");
			e1.printStackTrace();
		}
	}
	
	
	
	public Boolean sendMessage(String msg) {
		
		try {
			byte[] message = msg.getBytes();
			
			DataOutputStream dOut = new DataOutputStream(socket.getOutputStream());
			dOut.write(message);
			dOut.flush();  
		} catch (IOException e) {
			e.printStackTrace();
		}
        return true;
    }
	
	public Boolean ackReceive() {
        String msg = null;
		try {

	        byte[] buffer = new byte[1024];
            int len;
                 
            ByteArrayOutputStream byteArray = new ByteArrayOutputStream();
            InputStream is = socket.getInputStream();
            
            while ((len = is.read(buffer, 0, buffer.length)) != -1) {
            	System.out.println("Aqui");
            	byteArray.write(buffer, 0, len);
            }
            
            buffer = byteArray.toByteArray();
            msg = new String(buffer, "utf-8");
            
            if(msg.contentEquals("00")) {
            	System.out.println("Limite de canais conectados excedidos.");
            	return false;
            }
            System.out.println("Ack recebido: " + msg + " e " + buffer.length);
		} catch (IOException e) {
			e.printStackTrace();
			System.out.println("Erro no recebimento do ack.");
			return false;
		}
		return true;
	}
	
	public void receiverData() {
		try {
			System.out.println("Entrando para receber dados ...");
    		DataInputStream dis1 = new DataInputStream(socket.getInputStream());
			this.fileReceiver(dis1);
			
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	private void fileReceiver(DataInputStream dis) {
		try {
			InputStream is = socket.getInputStream();
			
    		// Recebe o arquivo
			
            byte[] buffer = new byte[1024];
            int len = 0;
    		int file_num = 0;
    		
    		ByteArrayOutputStream data = new ByteArrayOutputStream();
    		
    		while(is.available() != 0) {
	        	this.fileName = file_num + ".mkv";
	            FileOutputStream stream = new FileOutputStream("../../StreamVideo/"+ this.fileName + ".mkv");
	            BufferedOutputStream bos = new BufferedOutputStream(stream);
	            
	            while((len=is.read(buffer))!=-1)
	                bos.write(buffer, 0, len); 
	            
				file_num = file_num + 1;
				System.out.println("Nome do arquivo : " + this.fileName);
	
	            bos.flush(); 
    		}
		} catch (IOException e) {
			e.printStackTrace();
		}
		
	}

	
	
    public void stopConnection() {
        try {
			in.close();
	        out.close();
	        socket.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
    }
}
