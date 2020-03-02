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

import org.apache.karaf.shell.api.action.Argument;
import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onosproject.cli.AbstractShellCommand;

import java.io.InputStream;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.io.IOException;
import java.util.Base64;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;
import java.util.ArrayList;
import java.util.Iterator;
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

    static final String DEFAULT_NODES = "{"+
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

    static final String DEFAULT_LINKS = "{"+
                                            "\"links\" : {"+
                                                 "\"rest:127.0.0.1:9001/3-rest:127.0.0.1:9002/3\":{"+
                                                     "\"basic\" : {}"+
                                                 "},"+
                                                 "\"rest:127.0.0.1:9002/4-rest:127.0.0.1:9003/3\":{"+
                                                     "\"basic\" : {}"+
                                                 "}"+
                                             "}"+
                                        "}";

    @Argument(index = 0, name = "device-type",
            description = "configure device type: terminal/roadm/default-topo/monitor/osnr/show-links/show-roadm-links/show-terminal-links/show-router-links",
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
      }else if (device_type != null && device_type.equals("default-topo")) {
          default_topo ();
          print("Default Topology is %s", "Configured!");
      }else if (device_type != null && node_name != null && in_port != null && out_port != null && channel != null) {
          if (device_type.equals("roadm")){
            config_roadm(node_name,in_port,out_port,channel);
            print("ROADM configuration is %s", "done!");
          }else if (device_type.equals("ternimal") && power != null)
            config_terminal(node_name,in_port,out_port,channel,power);
            print("Terminal configuration is %s", "done!");
      }else if (device_type != null){
          print("Wrong arguments! Use one of the listed commands: %s", "terminal/roadm/default-topo/monitor/osnr/show-links/show-roadm-links/show-terminal-links/show-router-links");
      }
      return;
    }

    // generate new url with given key-value dictionary
    public static String urlFormat (String url, Map<String, String> dict) {
      String trail = "";
      for(String key: dict.keySet()){
          //System.out.println(key + ": " + dict.get(key));
          trail = trail + "&" + key + "=" + dict.get(key);
      }
      return url + "?" + trail.substring(1);
    }

    //set REST connection with url, username, and password
    public static HttpURLConnection RESTCon(String url, String usr, String psswd) {
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
    public static HttpURLConnection RESTCon(String url) {
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
    public static JsonNode conMethod (HttpURLConnection con, String method, String post_json) {
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
    public static JsonNode conMethod (HttpURLConnection con, String method, Map<String, String> dict, String post_json) {
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

    //generate a 3-terminal, 3-ROADM, 3-router network
    //       h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3
    //                      ||
    //                      t2 - s2 - h2
    public static void default_topo (){

      config_terminal("t1","1","3","1","0.0");
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
      config_roadm("r3","2","3","1");

      //post topo to ONOS
      Map<String, String> restproperties = new HashMap();
      restproperties.put("Content-Type","application/json");
      Map<String, String> del_restproperties = new HashMap();
      del_restproperties.put("Accepted","application/json");
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, DEFAULT_NODES); 
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, DEFAULT_LINKS); 
      try {
	    Thread.sleep(2000);
      } catch(InterruptedException e){
      }
      conMethod(RESTCon(ONOS_REST + LINKS, USR, PSWD), DELETE, del_restproperties, ""); 
      conMethod(RESTCon(ONOS_REST, USR, PSWD), POST, restproperties, DEFAULT_LINKS); 
      
      System.out.println("h1 - s1 - t1 = r1 --- r2 --- r3 = t3 - s3 - h3");
      System.out.println("                      ||");
      System.out.println("                      t2 - s2 - h2");
    }

    // configure roadm link
    public static void config_roadm (String name, String port1, String port2, String channels) {

      Map<String, String> node_info = new HashMap();
      node_info.put("node", name);node_info.put("port1", port1);node_info.put("port2", port2);node_info.put("channels", channels);
      String url = urlFormat("http://localhost:8080/connect", node_info);
      node_info.clear();
      conMethod(RESTCon (url), GET, "");
    }

    // configure terminal link
    public static void config_terminal (String name, String ethPort, String wdmPort, String channel, String power) {

      Map<String, String> t_info = new HashMap();
      t_info.put("node", name);t_info.put("ethPort", ethPort);t_info.put("wdmPort", wdmPort);t_info.put("channel", channel);t_info.put("power", power);
      String url = urlFormat("http://localhost:8080/connect", t_info);
      t_info.clear();
      conMethod(RESTCon (url), GET, "");
    }

    //monitors
    public void monitor () {

      String url = "http://localhost:8080/monitors";
      JsonNode monitors = conMethod(RESTCon (url), GET, "");
      KeyValue(monitors.get("monitors"));
    }

    //link osnr information
    public void osnr () {

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
        print(osnr.toString());

      }
    }

    //show all roadm-roadm links
    public void show_roadm_links () {

      String url = "http://localhost:8080" + LINKS + ROADMS;
      conMethod(RESTCon (url), GET, "");
      JsonNode links = conMethod(RESTCon (url), GET, "");
      KeyValue(links);
    }

    //show all terminal-roadm links
    public void show_terminal_links () {

      String url = "http://localhost:8080" + LINKS + TERMINALS;
      JsonNode links = conMethod(RESTCon (url), GET, "");
      KeyValue(links);
    }

    //show all router links
    public void show_router_links () {

      String url = "http://localhost:8080" + LINKS + "/routers";
      JsonNode links = conMethod(RESTCon (url), GET, "");
      KeyValue(links);
    }

    //show all terminal, roadm, router links
    public void show_links () {

      String url = "http://localhost:8080" + LINKS;
      JsonNode links = conMethod(RESTCon (url), GET, "");
      KeyValue(links);
    }

    public void KeyValue(JsonNode jsonNode) {

      for (Iterator<Map.Entry<String, JsonNode>> it = jsonNode.fields(); it.hasNext();){
        Map.Entry<String, JsonNode> field = it.next();
        print(field.getKey() + field.getValue().toString());
      }
    }

}
