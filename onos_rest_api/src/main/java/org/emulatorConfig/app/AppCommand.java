/*
########################################################
Author: Jiakai Yu
Affiliation: University of Arizona
Date: 02/2020
Project: ONOS REST API for Optical Emulator (with BoB Lantz, Alan Diaz Montiel)
########################################################
*/

/*
 * Copyright 2020-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.emulatorConfig.app;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;

import org.apache.karaf.shell.api.action.Argument;
import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onosproject.cli.AbstractShellCommand;

import java.io.InputStream;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.io.IOException;

import java.util.Arrays;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;
import java.util.List;
import java.util.Iterator;
import java.util.Random; 
import java.net.URL;
import java.net.HttpURLConnection;
import java.nio.charset.StandardCharsets;
import java.lang.Thread;
import java.lang.Iterable;


//use onos CLI
@Service
@Command(scope = "onos", name = "oe-config",
         description = "Optical Emulator Configure CLI command")
public class AppCommand extends AbstractShellCommand {

    static final String GET = "GET";
    static final String POST = "POST";
    static final String DELETE = "DELETE";
    static final String LINKS = "/links";
    static final String ROADMS = "/roadms";
    static final String TERMINALS = "/terminals";


    static final String ONOS_REST = "http://localhost:8181/onos/v1/network/configuration";
    static final String EMULATOR_REST = "http://localhost:8181/onos/v1/network/configuration";
    static final String USR = "onos";
    static final String PSWD = "rocks";

    static final String LINEAR_NODES = "{"+
                                          "\"devices\":{" + 
                                             "\"rest:127.0.0.1:9001\":{" + 
                                                "\"rest\": {" + 
                                                    "\"ip\": \"127.0.0.1\","+
                                                    "\"port\": 9001,"+
                                                    "\"username\": \"\","+
                                                    "\"password\": \"\","+
                                                    "\"protocol\": \"http\""+
                                                "},"+
                                                "\"basic\": {"+
                                                    "\"driver\": \"opticalemulator-roadm-rest\""+
                                                "}"+
                                              "},"+ 
                                             "\"rest:127.0.0.1:9002\":{" + 
                                                "\"rest\": {" + 
                                                    "\"ip\": \"127.0.0.1\","+
                                                    "\"port\": 9002,"+
                                                    "\"username\": \"\","+
                                                    "\"password\": \"\","+
                                                    "\"protocol\": \"http\""+
                                                "},"+
                                                "\"basic\": {"+
                                                    "\"driver\": \"opticalemulator-roadm-rest\""+
                                                "}"+
                                              "},"+ 
                                             "\"rest:127.0.0.1:9003\":{" + 
                                                "\"rest\": {" + 
                                                    "\"ip\": \"127.0.0.1\","+
                                                    "\"port\": 9003,"+
                                                    "\"username\": \"\","+
                                                    "\"password\": \"\","+
                                                    "\"protocol\": \"http\""+
                                                "},"+
                                                "\"basic\": {"+
                                                    "\"driver\": \"opticalemulator-roadm-rest\""+
                                                "}"+
                                             "}" +
                                           "}" +
                                        "}";

    static final String LINEAR_LINKS = "{"+
                                            "\"links\" : {"+
                                                 "\"rest:127.0.0.1:9001/3-rest:127.0.0.1:9002/3\":{"+
                                                     "\"basic\" : {}"+
                                                 "},"+
                                                 "\"rest:127.0.0.1:9002/4-rest:127.0.0.1:9003/3\":{"+
                                                     "\"basic\" : {}"+
                                                 "}"+
                                             "}"+
                                        "}";

      static final String DEMO_NODES = "{\"devices\": {\"rest:127.0.0.1:9001\": {\"rest\": {\"ip\": \"127.0.0.1\",\"port\": 9001,\"username\": \"\",\"password\": \"\",\"protocol\": \"http\"},\"basic\": {\"driver\": \"opticalemulator-roadm-rest\"}}, \"rest:127.0.0.1:9002\": {\"rest\": {\"ip\": \"127.0.0.1\",\"port\": 9002,\"username\": \"\",\"password\": \"\",\"protocol\": \"http\"},\"basic\": {\"driver\": \"opticalemulator-roadm-rest\"}}, \"rest:127.0.0.1:9006\": {\"rest\": {\"ip\": \"127.0.0.1\",\"port\": 9006,\"username\": \"\",\"password\": \"\",\"protocol\": \"http\"},\"basic\": {\"driver\": \"opticalemulator-roadm-rest\"}}, \"rest:127.0.0.1:9003\": {\"rest\": {\"ip\": \"127.0.0.1\",\"port\": 9003,\"username\": \"\",\"password\": \"\",\"protocol\": \"http\"},\"basic\": {\"driver\": \"opticalemulator-roadm-rest\"}}, \"rest:127.0.0.1:9004\": {\"rest\": {\"ip\": \"127.0.0.1\",\"port\": 9004,\"username\": \"\",\"password\": \"\",\"protocol\": \"http\"},\"basic\": {\"driver\": \"opticalemulator-roadm-rest\"}}, \"rest:127.0.0.1:9005\": {\"rest\": {\"ip\": \"127.0.0.1\",\"port\": 9005,\"username\": \"\",\"password\": \"\",\"protocol\": \"http\"},\"basic\": {\"driver\": \"opticalemulator-roadm-rest\"}}}}";

      static final String DEMO_LINKS = "{\"links\" : {\"rest:127.0.0.1:9001/2-rest:127.0.0.1:9002/1\":{\"basic\" : {}}, \"rest:127.0.0.1:9002/2-rest:127.0.0.1:9003/1\":{\"basic\" : {}}, \"rest:127.0.0.1:9003/2-rest:127.0.0.1:9001/1\":{\"basic\" : {}}, \"rest:127.0.0.1:9004/2-rest:127.0.0.1:9005/1\":{\"basic\" : {}}, \"rest:127.0.0.1:9005/2-rest:127.0.0.1:9006/1\":{\"basic\" : {}}, \"rest:127.0.0.1:9006/2-rest:127.0.0.1:9004/1\":{\"basic\" : {}}, \"rest:127.0.0.1:9002/4-rest:127.0.0.1:9004/3\":{\"basic\" : {}}, \"rest:127.0.0.1:9003/4-rest:127.0.0.1:9005/3\":{\"basic\" : {}}}}";


    @Argument(index = 0, name = "device-type",
            description = "configure device type: terminal/roadm/monitor/osnr/demo-topo/linear-topo/demo-flows/demo-mesh-flows/clean-flows/reset/add-flow/set-gain/show-ports/show-nodes/show-links/show-roadm-links/show-terminal-links/show-router-links",
            required = true, multiValued = false)
    String device_type = null;

    @Argument(index = 1, name = "names", description = "device name",
            required = false, multiValued = false)
    String node_name = null;

    @Argument(index = 2, name = "input-port-id", description = "signal input port id",
            required = false, multiValued = false)
    String in_port = null;

    @Argument(index = 3, name = "output-port-id", description = "signal output port id",
            required = false, multiValued = false)
    String out_port = null;

    @Argument(index = 4, name = "channel-id", description = "occupied channel id",
            required = false, multiValued = false)
    String channel = null;

    @Argument(index = 5, name = "power", description = "device name",
            required = false, multiValued = false)
    String power = null;

    @Override
    protected void doExecute() {

      print("Optical Emulator CLI %s", "is activated!");

      if (device_type != null && device_type.equals("show-links")) {
          print("All Links %s", "are listed as below:");
          show_links ();
      }else if (device_type != null && device_type.equals("show-nodes")){
          print("All Nodes %s", "are listed as below:");
          show_nodes ();
      }else if (device_type != null && device_type.equals("show-roadm-links")){
          print("All ROADM Links %s", "are listed as below:");
          show_roadm_links ();
      }else if (device_type != null && device_type.equals("show-router-links")){
          print("All Router Links %s", "are listed as below:");
          show_router_links ();
      }else if (device_type != null && device_type.equals("show-terminal-links")){
          print("All Terminal Links %s", "are listed as below:");
          show_terminal_links ();
      }else if (device_type != null && device_type.equals("monitor")){
          print("Network Monitored Infomation %s", ":");
          monitor ();
      }else if (device_type != null && device_type.equals("osnr")){
          print("Link OSNR Infomation %s", ":");
          osnr ();
      }else if (device_type != null && device_type.equals("demo-topo")) {
          demo_topo ();
          print("Demo Topology is %s", "Configured!");
      }else if (device_type != null && device_type.equals("linear-topo")) {
          linear_topo ();
          print("Linear Topology is %s", "Configured!");
      }else if (device_type != null && device_type.equals("clean-flows")) {
          clean_flow ();
          print("Demo Network Flows are %s", "Cleaned!");
      }else if (device_type != null && device_type.equals("demo-flows")) {
          demo_flow ();
          print("Demo Network Flows are %s", "Generated!");
      }else if (device_type != null && device_type.equals("demo-link-recovery")) {
          demo_link_recovery ();
          print("Demo Failure Links are %s", "Recovered!");
      }else if (device_type != null && device_type.equals("demo-mesh-flows")) {
          demo_mesh_flow ();
          print("Mesh Network Flows are %s", "Generated!");
      }else if (device_type != null && device_type.equals("reset") && node_name != null) {
          reset_roadm (node_name);
          print("ROADM Reset is %s", "Completed!");
      }else if (device_type != null && device_type.equals("show-ports") && node_name != null) {
          print("ROADM Ports are %s", "Listed!");
          show_roadm_ports (node_name);
      }else if (device_type != null && device_type.equals("add-flow") && node_name != null && in_port != null) {
          add_flow (node_name, in_port, out_port, channel);
          print("Added Flow is %s", "Completed!");
      }else if (device_type != null && device_type.equals("set-gain") && node_name != null && in_port != null) {
          set_gain (node_name, in_port);
          print("Amplifier Gain is %s", "Set!");
      }else if (device_type != null && node_name != null && in_port != null && out_port != null && channel != null) {
          if (device_type.equals("roadm")){
            config_roadm(node_name,in_port,out_port,channel);
            print("ROADM configuration is %s", "done!");
          }else if (device_type.equals("terminal") && power != null){
            config_terminal(node_name,in_port,out_port,channel,power);
            print("Terminal configuration is %s", "done!");
          }
      }else if (device_type != null){
          print("Wrong arguments! Use one of the listed commands: %s", "\n"+"terminal/roadm/monitor/osnr/" +"\n"+"demo-topo/linear-topo/demo-flows/demo-mesh-flows/clean-flows/"+"\n"+"reset/add-flow/set-gain/"+"\n"+"show-nodes/show-ports/show-links/show-roadm-links/show-terminal-links/show-router-links");
      }
      return;
    }

    // generate new url with given key-value dictionary
    private static String urlFormat (String url, Map<String, String> dict) {
      String trail = "";
      for(String key: dict.keySet()){
          //System.out.println(key + ": " + dict.get(key));
          trail = trail + "&" + key + "=" + dict.get(key);
      }
      return url + "?" + trail.substring(1);
    }

    //set REST connection with url, username, and password
    private static HttpURLConnection RESTCon(String url, String usr, String psswd) {
      try{
        String urly = url;
	URL obj = new URL(urly);
	HttpURLConnection con = (HttpURLConnection) obj.openConnection();
	String auth = usr + ":" + psswd;
        final byte[] authBytes = auth.getBytes(StandardCharsets.UTF_8);
        final String encodedAuth = Base64.getEncoder().encodeToString(authBytes);
	String authHeaderValue = "Basic " + new String(encodedAuth);
	con.setRequestProperty("Authorization", authHeaderValue);
	con.setDoOutput(true);
        return con;
      }catch (Exception e) {
        e.printStackTrace();
      }
      return null;
    }

    //set REST connection with url
    private static HttpURLConnection RESTCon(String url) {
      try{
	String urly = url;
	URL obj = new URL(urly);
	HttpURLConnection con = (HttpURLConnection) obj.openConnection();
	con.setDoOutput(true);
        return con;
      }catch (Exception e) {
        e.printStackTrace();
      }
      return null;
    }

    //REST connection with GET/POST/DELETE method
    private static JsonNode conMethod (HttpURLConnection con, String method, String post_json) {
      try{
	con.setRequestMethod(method);
        if(method.equals("GET") || method.equals("DELETE") ) {
   	  con.connect();     
        }
        if(method.equals("POST")) {
	  DataOutputStream wr = new DataOutputStream(con.getOutputStream());
	  wr.writeBytes(post_json);
	  wr.flush();
	  wr.close();
        }
	int responseCode = con.getResponseCode();
	//System.out.println("Response Code : " + responseCode);
	BufferedReader iny = new BufferedReader(
	new InputStreamReader(con.getInputStream()));
	  String output;
	  StringBuffer response = new StringBuffer();

	  while ((output = iny.readLine()) != null) {
	   response.append(output);
	  }
	  iny.close();
	  //printing result from response
	  
          try{
            ObjectMapper om = new ObjectMapper();
            JsonNode json = om.readTree(response.toString());
            //JsonNode res = json.get(RESULT);
              //JSONParser parser = new JSONParser();
              //JSONObject json = (JSONObject) parser.parse(response.toString());
            //System.out.println(json);
            return json;
          }catch (Exception e) {
             //System.out.println(response.toString());
             //e.printStackTrace();
             return null;
          }
      }catch (Exception e) {
        //e.printStackTrace();
        return null;
      }
    }

    //set REST connection with GET/POST/DELETE method, and properties of map dict
    private static JsonNode conMethod (HttpURLConnection con, String method, Map<String, String> dict, String post_json) {
      try{
        for(String key: dict.keySet()){
            //System.out.println(key + ": " + dict.get(key));
            con.setRequestProperty(key, dict.get(key));
        }
	con.setRequestMethod(method);
        if(method.equals("GET") || method.equals("DELETE")) {
   	  con.connect();     
        }
        if(method.equals("POST")) {
	  DataOutputStream wr = new DataOutputStream(con.getOutputStream());
	  wr.writeBytes(post_json);
	  wr.flush();
	  wr.close();
        }
	int responseCode = con.getResponseCode();
	//System.out.println("Response Code : " + responseCode);

	BufferedReader iny = new BufferedReader(
	new InputStreamReader(con.getInputStream()));
	  String output;
	  StringBuffer response = new StringBuffer();

	  while ((output = iny.readLine()) != null) {
	   response.append(output);
	  }
	  iny.close();
	  //printing result from response
	  
          try{
            ObjectMapper om = new ObjectMapper();
            JsonNode json = om.readTree(response.toString());
            //JsonNode res = json.get(RESULT);
              //JSONParser parser = new JSONParser();
              //JSONObject json = (JSONObject) parser.parse(response.toString());
            //System.out.println(json);
            return json;
          }catch (Exception e) {
            //System.out.println(response.toString());
            //e.printStackTrace();
            return null;
          }
      }catch (Exception e) {
        //e.printStackTrace();
        return null;
      }
    }



    //setgain for a amplifier
    public static void set_gain(String amp, String gain) {
             
             String url = String.format("http://localhost:8080/setgain?amplifier=%s&gain=%s",amp, gain);
             JsonNode links = conMethod(RESTCon (url), GET, "");
    }

    //add a single flow from a router to router through optical layer
    public static void add_flow(String source, String destination, String chnnl, String power) {

             String url = "http://localhost:8080" + LINKS;
             JsonNode links = conMethod(RESTCon (url), GET, "");
             List<String[]> link_map = new ArrayList<String[]>();
             traverse(links, link_map);
             String[][] conn = new String[link_map.size()-1][4];
             for(int i =0; i < link_map.size()-1;i++)
                conn[i] = link_map.get(i);

             DijkstraMain dijkstra = new DijkstraMain();
             String[] routers = new String[] {"s1", "s2", "s3", "s4", "s5", "s6"};
             Random rand = new Random();
             List<String> path_p = new ArrayList<String>();
             if (chnnl ==null){
                 int channel = rand.nextInt(40);
                 chnnl = String.valueOf(channel);
             }
             if (power ==null){
                 power = "0.0";
             }
             String src = source;
             String dst = destination;
             System.out.println(src + "--" + dst + ":" + chnnl + "/"+ power);
             path_p = dijkstra.dijkstraPath(conn, src, dst);
             System.out.println("Light-path: " + path_p);
	     for (int i = 2; i< path_p.size();i+=4){
	       if (path_p.get(i).startsWith("t")){
	         if(i!= path_p.size()-6)
	           config_terminal(path_p.get(i),path_p.get(i+1),path_p.get(i+3),chnnl,power);
	         else if(i== path_p.size()-6)
		   config_terminal(path_p.get(i),path_p.get(i+3),path_p.get(i+1),chnnl,power);
	       }
	       if (path_p.get(i).startsWith("r")){
	         if(i!= path_p.size()-6)
	           config_roadm(path_p.get(i),path_p.get(i+1),path_p.get(i+3),chnnl);
	         else if(i== path_p.size()-6)
	           config_roadm(path_p.get(i),path_p.get(i+3),path_p.get(i+1),chnnl);
	       }
	     }

    }


    //clean all flows
    public static void clean_flow() {
   
             reset_roadm ("r1");
             reset_roadm ("r2");
             reset_roadm ("r3");
             reset_roadm ("r4");
             reset_roadm ("r5");
             reset_roadm ("r6");


    }


    //add demi flows from a router to router through optical layer
    public static void demo_link_recovery() {

             int count = 0;

             while (count!=5) {
             int port11 = 1;
             int port12 = 16;
             int port21 = 1;
             int port22 = 16;
             int chnnl = 6;
             //t1-r1-r2-r4-r6-t6 with ch1-ch5
             //config_terminal("t1", String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             //config_terminal("t6", String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             del_roadm("r1",String.valueOf(port11+count),"16",String.valueOf(chnnl+count));
             del_roadm("r2","16","17",String.valueOf(chnnl+count));
             del_roadm("r4","17","16",String.valueOf(chnnl+count));
             del_roadm("r6","17",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;


             while (count!=5) {
             int port11 = 11;
             int port12 = 26;
             int port21 = 11;
             int port22 = 26;
             int chnnl = 1;
             //t1-r1-r2-r4-r5-t5 with ch21-ch25
             //config_terminal("t1",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             //config_terminal("t5",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             del_roadm("r1",String.valueOf(port11+count),"16",String.valueOf(chnnl+count));
             del_roadm("r2","16","17",String.valueOf(chnnl+count));
             del_roadm("r4","17","18",String.valueOf(chnnl+count));
             del_roadm("r5","18",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

             while (count!=5) {
             int port11 = 6;
             int port12 = 21;
             int port21 = 6;
             int port22 = 21;
             int chnnl = 6;
             //t1-r1-r3-r5-r6-t6 with ch6-ch10
             config_terminal("t1",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t6",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r1",String.valueOf(port11+count),"17",String.valueOf(chnnl+count));
             config_roadm("r3","16","17",String.valueOf(chnnl+count));
             config_roadm("r5","16","17",String.valueOf(chnnl+count));
             config_roadm("r6","16",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;


             while (count!=5) {
             int port11 = 11;
             int port12 = 26;
             int port21 = 11;
             int port22 = 26;
             int chnnl = 1;
             //t1-r1-r3-r5-r6-t6 with ch6-ch10
             config_terminal("t1",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t5",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r1",String.valueOf(port11+count),"17",String.valueOf(chnnl+count));
             config_roadm("r3","16","17",String.valueOf(chnnl+count));
             config_roadm("r5","16",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

    }


    //add demi flows from a router to router through optical layer
    public static void demo_flow() {

             String url = "http://localhost:8080" + LINKS;
             JsonNode links = conMethod(RESTCon (url), GET, "");
             List<String[]> link_map = new ArrayList<String[]>();
             traverse(links, link_map);
             String[][] conn = new String[link_map.size()-1][4];
             for(int i =0; i < link_map.size()-1;i++)
                conn[i] = link_map.get(i);

             int count = 0;

             while (count!=5) {
             int port11 = 1;
             int port12 = 16;
             int port21 = 1;
             int port22 = 16;
             int chnnl = 6;
             //t1-r1-r2-r4-r6-t6 with ch1-ch5
             config_terminal("t1", String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t6", String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r1",String.valueOf(port11+count),"16",String.valueOf(chnnl+count));
             config_roadm("r2","16","17",String.valueOf(chnnl+count));
             config_roadm("r4","17","16",String.valueOf(chnnl+count));
             config_roadm("r6","17",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

             while (count!=5) {
             int port11 = 6;
             int port12 = 21;
             int port21 = 6;
             int port22 = 21;
             int chnnl = 21;
             //t1-r1-r3-r5-r6-t6 with ch6-ch10
             config_terminal("t1",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t6",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r1",String.valueOf(port11+count),"17",String.valueOf(chnnl+count));
             config_roadm("r3","16","17",String.valueOf(chnnl+count));
             config_roadm("r5","16","17",String.valueOf(chnnl+count));
             config_roadm("r6","16",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

             while (count!=5) {
             int port11 = 11;
             int port12 = 26;
             int port21 = 11;
             int port22 = 26;
             int chnnl = 1;
             //t1-r1-r2-r4-r5-t5 with ch21-ch25
             config_terminal("t1",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t5",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r1",String.valueOf(port11+count),"16",String.valueOf(chnnl+count));
             config_roadm("r2","16","17",String.valueOf(chnnl+count));
             config_roadm("r4","17","18",String.valueOf(chnnl+count));
             config_roadm("r5","18",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

             while (count!=5) {
             int port11 = 1;
             int port12 = 16;
             int port21 = 1;
             int port22 = 16;
             int chnnl = 16;
             //t3-r3-r2-r4-t4 with ch11-ch15
             config_terminal("t3",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t4",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r3",String.valueOf(port11+count),"18",String.valueOf(chnnl+count));
             config_roadm("r2","18","17",String.valueOf(chnnl+count));
             config_roadm("r4","17",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

             while (count!=5) {
             int port11 = 6;
             int port12 = 21;
             int port21 = 1;
             int port22 = 16;
             int chnnl = 26;
             //t4-r4-r5-t5 with ch16-ch20
             config_terminal("t4",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t5",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r4",String.valueOf(port11+count),"18",String.valueOf(chnnl+count));
             config_roadm("r5","18",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

             while (count!=5) {
             int port11 = 1;
             int port12 = 16;
             int port21 = 11;
             int port22 = 26;
             int chnnl = 21;
             //t2-r2-r4-r6-t6 with ch16-ch20
             config_terminal("t2",String.valueOf(port11+count), String.valueOf(port12+count),String.valueOf(chnnl+count),"0.0");
             config_terminal("t6",String.valueOf(port21+count), String.valueOf(port22+count),String.valueOf(chnnl+count),"0.0");
             config_roadm("r2",String.valueOf(port11+count),"17",String.valueOf(chnnl+count));
             config_roadm("r4","17","16",String.valueOf(chnnl+count));
             config_roadm("r6","17",String.valueOf(port21+count),String.valueOf(chnnl+count));
             count++;
             }
             count = 0;

    }




    //add mesh network flows from a router to router through optical layer
    public static void demo_mesh_flow() {
             int count =2;
             int gap = 10;
             String url = "http://localhost:8080" + LINKS;
             JsonNode links = conMethod(RESTCon (url), GET, "");
             List<String[]> link_map = new ArrayList<String[]>();
             traverse(links, link_map);
             String[][] conn = new String[link_map.size()-1][4];
             for(int i =0; i < link_map.size()-1;i++)
                conn[i] = link_map.get(i);

             DijkstraMain dijkstra = new DijkstraMain();
             String[] routers = new String[] {"s1", "s2", "s3", "s4", "s5", "s6"};
             Random rand = new Random();
             List<String> path_p = new ArrayList<String>();
             int channel = rand.nextInt(10);
             for (int n =0; n<routers.length;n++){
               for (int m =n+1; m<routers.length;m++){
                 if (n!=m){
                   String src = routers[n];
                   String dst = routers[m];

	           path_p = dijkstra.dijkstraPath(conn, src, dst);
                   //System.out.println(src +"-" + dst + ":" + chnnl);
                  while(count!=0){
                   String chnnl = String.valueOf(channel+gap);
                   gap += 20;
		   for (int i = 2; i< path_p.size();i+=4){
				    //System.out.println(path_p);
		     if (path_p.get(i).startsWith("t")){
		       if(i!= path_p.size()-6)
		         config_terminal(path_p.get(i),path_p.get(i+1),path_p.get(i+3),chnnl,"0.0");
		       else if(i== path_p.size()-6)
			 config_terminal(path_p.get(i),path_p.get(i+3),path_p.get(i+1),chnnl,"0.0");
		     }
		     if (path_p.get(i).startsWith("r")){
		       if(i!= path_p.size()-6)
		         config_roadm(path_p.get(i),path_p.get(i+1),path_p.get(i+3),chnnl);
		       else if(i== path_p.size()-6)
		         config_roadm(path_p.get(i),path_p.get(i+3),path_p.get(i+1),chnnl);
		     }
		   }

                   count--;
                  }
                  channel++;
                  count=3;
                  gap = 0;
                 }
               }
             }
    }


    //generate a 3-terminal, 3-ROADM, 3-router network
    //       h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3
    //                      ||
    //                      t2 - s2 - h2
    private static void linear_topo (){

      /*config_terminal("t1","1","3","1","0.0");
      config_terminal("t1","2","4","2","0.0");
      config_terminal("t2","1","3","1","0.0");
      config_terminal("t2","2","4","1","0.0");
      config_terminal("t3","1","3","2","0.0");
      config_terminal("t3","2","4","1","0.0");
      config_roadm("r1","1","3","1");
      config_roadm("r1","2","3","2");
      config_roadm("r2","1","3","1");
      config_roadm("r2","2","4","1");
      config_roadm("r2","3","4","2");
      config_roadm("r3","1","3","2");
      config_roadm("r3","2","3","1");*/

      //post topo to ONOS
      Map<String, String> restproperties = new HashMap();
      restproperties.put("Content-Type","application/json");
      Map<String, String> del_restproperties = new HashMap();
      del_restproperties.put("Accepted","application/json");
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, LINEAR_NODES); 
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, LINEAR_LINKS); 
      try {
	    Thread.sleep(2000);
      } catch(InterruptedException e){
      }
      conMethod(RESTCon(ONOS_REST + LINKS, USR, PSWD), DELETE, del_restproperties, ""); 
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, LINEAR_LINKS); 
      
      System.out.println("h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3");
      System.out.println("                      ||");
      System.out.println("                      t2 - s2 - h2");
    }


    //generate a DEMO 6-ROADM, 6-router network
    //         POP2 -- POP4
    //        /  |      |  \
    //       /   |      |   \
    //   POP1    |      |    POP6
    //       \   |      |   /
    //        \  |      |  /
    //         POP3 -- POP5
    private static void demo_topo (){

      //post topo to ONOS
      Map<String, String> restproperties = new HashMap();
      restproperties.put("Content-Type","application/json");
      Map<String, String> del_restproperties = new HashMap();
      del_restproperties.put("Accepted","application/json");
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, DEMO_NODES); 
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, DEMO_LINKS); 
      try {
	    Thread.sleep(2000);
      } catch(InterruptedException e){
      }
      conMethod(RESTCon(ONOS_REST + LINKS, USR, PSWD), DELETE, del_restproperties, ""); 
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, DEMO_LINKS); 
      
      System.out.println("             POP2 -- POP4");
      System.out.println("            /  |      |  \\ ");
      System.out.println("           /   |      |   \\ ");
      System.out.println("       POP1    |      |    POP6");
      System.out.println("           \\   |      |   /");
      System.out.println("            \\  |      |  /");
      System.out.println("             POP3 -- POP5");
    }

    // configure roadm link
    private static void config_roadm (String name, String port1, String port2, String channels) {

      Map<String, String> node_info = new HashMap();
      node_info.put("node", name);node_info.put("port1", port1);node_info.put("port2", port2);node_info.put("channels", channels);
      String url = urlFormat("http://localhost:8080/connect", node_info);
      node_info.clear();
      conMethod(RESTCon (url), GET, "");
    }

    // configure terminal link
    private static void config_terminal (String name, String ethPort, String wdmPort, String channel, String power) {

      Map<String, String> t_info = new HashMap();
      t_info.put("node", name);t_info.put("ethPort", ethPort);t_info.put("wdmPort", wdmPort);t_info.put("channel", channel);t_info.put("power", power);
      String url = urlFormat("http://localhost:8080/connect", t_info);
      t_info.clear();
      conMethod(RESTCon (url), GET, "");
    }


    // del roadm link
    private static void del_roadm (String name, String port1, String port2, String channels) {

      Map<String, String> node_info = new HashMap();
      node_info.put("node", name);node_info.put("port1", port1);node_info.put("port2", port2);node_info.put("channels", channels);
      String url = urlFormat("http://localhost:8080/connect", node_info);
      node_info.clear();
      conMethod(RESTCon (url+"&action=remove"), GET, "");
    }

    // del terminal link
    private static void del_terminal (String name, String ethPort, String wdmPort, String channel, String power) {

      Map<String, String> t_info = new HashMap();
      t_info.put("node", name);t_info.put("ethPort", ethPort);t_info.put("wdmPort", wdmPort);t_info.put("channel", channel);t_info.put("power", power);
      String url = urlFormat("http://localhost:8080/connect", t_info);
      t_info.clear();
      conMethod(RESTCon (url+"&action=remove"), GET, "");
    }


    //monitors
    private void monitor () {

      String url = "http://localhost:8080/monitors";
      JsonNode monitors = conMethod(RESTCon (url), GET, "");
      //KeyValue(monitors);
      KeyValue(monitors.get("monitors"));
      List<String[]> monitor_map = new ArrayList<String[]>();
      //traverse(monitors.get("monitors").get("osnr"), monitor_map);
      //for(int i =0; i < monitor_map.size()-1;i++)
        //print(Arrays.toString(monitor_map.get(i)));
    }

    //link osnr information
    private void osnr () {

      String url = "http://localhost:8080/monitors";
      JsonNode monitors = conMethod(RESTCon (url), GET, "");
      JsonNode jsonNode = monitors.get("monitors");
      for (Iterator<Map.Entry<String, JsonNode>> it = jsonNode.fields(); it.hasNext();){
        Map.Entry<String, JsonNode> field = it.next();
        //print(field.getKey() + field.getValue().toString());
        Map<String, String> node_info = new HashMap();
        node_info.put("monitor", field.getKey());
        String url1 = urlFormat("http://localhost:8080/monitor", node_info);
        node_info.clear();
        JsonNode osnr = conMethod(RESTCon (url1), GET, "");
        print(field.getValue().toString());
        //print(osnr.toString());
        KeyValue(osnr.get("osnr"));

      }

    }

    //reset a roadm links
    private static void reset_roadm (String Node) {

      String url = "http://localhost:8080" + "/reset?node=" + Node;
      conMethod(RESTCon (url), GET, "");
      conMethod(RESTCon (url), GET, "");

    }


    //show all roadm ports
    private void show_roadm_ports (String Node) {

      String url = "http://localhost:8080" + "/ports?node=" + Node;
      conMethod(RESTCon (url), GET, "");
      JsonNode ports = conMethod(RESTCon (url), GET, "");
      KeyValue(ports);

    }

    //show all roadm-roadm links
    private void show_roadm_links () {

      String url = "http://localhost:8080" + LINKS + ROADMS;
      conMethod(RESTCon (url), GET, "");
      JsonNode links = conMethod(RESTCon (url), GET, "");
      //KeyValue(links);
      List<String[]> link_map = new ArrayList<String[]>();
      traverse(links, link_map);
      for(int i =0; i < link_map.size()-1;i++)
        //print(Arrays.toString(link_map.get(i)));
        print(link_map.get(i)[0]+"/"+link_map.get(i)[1]+" <-> "+link_map.get(i)[2]+"/"+link_map.get(i)[3]);
    }

    //show all terminal-roadm links
    private void show_terminal_links () {

      String url = "http://localhost:8080" + LINKS + TERMINALS;
      JsonNode links = conMethod(RESTCon (url), GET, "");
      //KeyValue(links);
      List<String[]> link_map = new ArrayList<String[]>();
      traverse(links, link_map);
      for(int i =0; i < link_map.size()-1;i++)
        //print(Arrays.toString(link_map.get(i)));
        print(link_map.get(i)[0]+"/"+link_map.get(i)[1]+" <-> "+link_map.get(i)[2]+"/"+link_map.get(i)[3]);
    }

    //show all router links
    private void show_router_links () {

      String url = "http://localhost:8080" + LINKS + "/routers";
      JsonNode links = conMethod(RESTCon (url), GET, "");
      //KeyValue(links);
      List<String[]> link_map = new ArrayList<String[]>();
      traverse(links, link_map);
      for(int i =0; i < link_map.size()-1;i++)
        //print(Arrays.toString(link_map.get(i)));
        print(link_map.get(i)[0]+"/"+link_map.get(i)[1]+" <-> "+link_map.get(i)[2]+"/"+link_map.get(i)[3]);

    }


    //show all terminal, roadm, router links
    private void show_links () {

      String url = "http://localhost:8080" + LINKS;
      JsonNode links = conMethod(RESTCon (url), GET, "");
      //KeyValue(links);
      List<String[]> link_map = new ArrayList<String[]>();
      traverse(links, link_map);
      for(int i =0; i < link_map.size()-1;i++)
        //print(Arrays.toString(link_map.get(i)));
        print(link_map.get(i)[0]+"/"+link_map.get(i)[1]+" <-> "+link_map.get(i)[2]+"/"+link_map.get(i)[3]);
    }

    //show all nodes
    private void show_nodes () {

      String url = "http://localhost:8080" + "/nodes";
      JsonNode nodes = conMethod(RESTCon (url), GET, "");
      KeyValue(nodes.get("nodes"));
      //List<String[]> node_map = new ArrayList<String[]>();
      //traverse(nodes, node_map);
      //for(int i =0; i < node_map.size()-1;i++)
        //print(Arrays.toString(node_map.get(i)));
        //print(node_map.get(i)[0]+":"+node_map.get(i)[1]);

    }

    private Map<String,JsonNode> KeyValue(JsonNode jsonNode) {
      //List<Map<String,JsonNode>> kv = new ArrayList<HashMap<String,JsonNode>>();
      Map<String, JsonNode> map = new HashMap<>();
      for (Iterator<Map.Entry<String, JsonNode>> it = jsonNode.fields(); it.hasNext();){
        Map.Entry<String, JsonNode> field = it.next();
        print(field.getKey() + ":" + field.getValue().toString());
        map.put(field.getKey(), field.getValue());
        //kv.add(map);
        //map.clear();
      }
      return map;
    }

    // traverse JsonNode
    private static void traverse(JsonNode root, List<String[]> link_map){
      //List<String[]> link_map = new ArrayList<String[]>();
      if(root.isObject()){
        Iterator<String> fieldNames = root.fieldNames();
        List<String> conn = new ArrayList<String>();
        while(fieldNames.hasNext()) {
            String fieldName = fieldNames.next();
            JsonNode fieldValue = root.get(fieldName);
            //print(fieldName + ":" + fieldValue.toString());
            conn.add(fieldName);
            conn.add(fieldValue.toString());
            traverse(fieldValue, link_map);
            
        }
        String[] links = new String[conn.size()];
        links = conn.toArray(links);
        link_map.add(links);
        //print(Arrays.toString(links));


      } else if(root.isArray()){
        ArrayNode arrayNode = (ArrayNode) root;
        for(int i = 0; i < arrayNode.size(); i++) {
            JsonNode arrayElement = arrayNode.get(i);
            //print(arrayElement.toString());
            traverse(arrayElement, link_map);

        }
      } else {
        // JsonNode root represents a single value field - should do something with it?
        
      }
    }

}


