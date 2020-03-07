package org.emulatorConfig.app;
import java.util.ArrayList;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Arrays;
import java.util.PriorityQueue;
import java.util.HashMap;
import java.util.Map;
import java.util.Random; 

public class DijkstraMain {

	public static List<String> dijkstraPath(String[][] conn, String source, String destination) {

                Map<String, Vertex> Nodes_Map = new HashMap<String, Vertex>();
                for(int i=0; i<conn.length; i++){
                    if(!Nodes_Map.containsKey(conn[i][0]))
                       Nodes_Map.put(conn[i][0], new Vertex(conn[i][0]));
                    if(!Nodes_Map.containsKey(conn[i][2]))
                       Nodes_Map.put(conn[i][2], new Vertex(conn[i][2]));
                    Nodes_Map.get(conn[i][0]).addNeighbour(new Edge(1,Nodes_Map.get(conn[i][0]),Nodes_Map.get(conn[i][2])));
                    Nodes_Map.get(conn[i][2]).addNeighbour(new Edge(1,Nodes_Map.get(conn[i][2]),Nodes_Map.get(conn[i][0])));
                }
                Vertex SRC = Nodes_Map.get(source);
                Vertex DST = Nodes_Map.get(destination);
		DijkstraShortestPath shortestPath = new DijkstraShortestPath();
		shortestPath.computeShortestPaths(SRC);
                List<Vertex> shotest_paths = shortestPath.getShortestPathTo(DST);
                List<String> path_p = new ArrayList<String>();
                int path_len = shotest_paths.size();
                for(int i = 0; i<path_len-1;i++){
                    String start = shotest_paths.get(i).getName();
                    String end = shotest_paths.get(i+1).getName();
                    //System.out.println(start + "-" + end);
                    for(int j =0; j<conn.length;j++){
                        if(conn[j][0].equals(start) && conn[j][2].equals(end)){
                            path_p.add(start);
                            path_p.add(conn[j][1]);
                            path_p.add(end);
                            path_p.add(conn[j][3]);
                            if ( end.startsWith("t") || start.startsWith("t") ) {
                                conn[j][0] = "#"+conn[j][0];
                                conn[j][2] = "#"+conn[j][2];
                                //System.out.println(conn[j][0]+":"+conn[j][1] +"-" + conn[j][2]+":"+conn[j][3]);
                            }
                            break;
                        }    
                        if(conn[j][0].equals(end) && conn[j][2].equals(start)){
                            //System.out.println(start+":"+conn[j][3] + "-" + end+ ":" +conn[j][1]);
                            path_p.add(start);
                            path_p.add(conn[j][3]);
                            path_p.add(end);
                            path_p.add(conn[j][1]);
                            if ( end.startsWith("t") || start.startsWith("t") ) {
                                conn[j][0] = "#"+conn[j][0];
                                conn[j][2] = "#"+conn[j][2];
                                //System.out.println(conn[j][0]+":"+conn[j][1] +"-" + conn[j][2]+":"+conn[j][3]);
                            }
                            break;
                        }    
                    }               
                }
                return path_p;
	}
}
