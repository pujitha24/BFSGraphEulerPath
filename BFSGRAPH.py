#NAME        : P PUJITHA SRI LAKSHMI PALADUGU
#NET ID      : PXP142730
#DATE STARTED: 2/1/2014.
#PURPOSE     : This is the assignment for the class CS6364
#Design an intelligent agent to draw a continuous line covering all the links from node A to node A and node A to anywhere.
#DESCRPTION   :This module mainly find the path using Breadth first search. The function takes input as two graphs staring node and no of edges
#it find the path starting from node A to node A and node A to anywhere.


__author__ = 'pujitha'
# This function gets the graph and expands all parent nodes, stores  in the queue and removes the first element from the queue and checks
# if there is an edge between two edges. if edge exists, then path list is appended. This process  is repeated until all links of graph
#are covered only once.

def bfs(graph, start, edge):

 visited,queue= [],[start]
 path=[]
 nodes_exp=0;
 for node in sorted(graph):
  for i in range(0,len(graph[node])):
      u=graph[node][i]
      queue.append(u)
  nodes_exp=nodes_exp+1
 path.append(queue.pop(0))
 while queue:
     k=path[-1]
     vertex=queue.pop(0)
     try:
      ver=graph[k][graph[k].index(vertex)]
      val=graph[vertex][graph[vertex].index(k)]
     except ValueError:

      pass

     if ver== vertex and val==k:
           path.append(vertex)
           del graph[vertex][graph[vertex].index(k)]
           del graph[k][graph[k].index(vertex)]

     else:
          continue
 list3=[]

 while  len(path)< edge:
   last =path[-1]
   m=len(graph[last])
   for i in range(0,m):
    try:
     if graph[last][i]:
      m=m-1
      path.append(graph[last][i])
      del graph[last][i]
    except IndexError:
      pass
 path.append(nodes_exp)
 return path
#Main module: it calls bfs and stores path in a list and prints the list.
def main():
  print("--------------------------------------------------------------------------------------------------------------")
  print ("Solution for Graph1 in BFS")
  list1=list(bfs(graph,'A',9))
  nodes_ex=list1.pop()
  if (list1[-1]== 'A'):

     print("path exist from source node 'A' to 'A' only"+" and Path is:")
     print list1
     print("Solution:")
     list3=[]
     list3.extend([list1[0],list1[1],nodes_ex,nodes_ex,nodes_ex,list1[-1]])
     print(list3)
     print("No path exist from source node 'A' to other nodes")
     print("No Solution")

  else:

    print("path exist from source node 'A' to other nodes"+" and Path is:")
    print list1
    print("Solution:")
    list3=[]
    list3.extend([list1[0],list1[1],nodes_ex,nodes_ex,nodes_ex,list1[-1]])
    print(list3)
    print("No path exist from source node 'A' to 'A'")
    print("No Solution")

  print("--------------------------------------------------------------------------------------------------------------")
  print("Solution for Graph2 in BFS")
  list2=list(bfs(graph2,'A',11))
  nodes_ex=list2.pop()
  if (list2[-1]== 'A'):

     print("path exist from source node 'A' to 'A' only"+" and Path is:")
     print list2
     print("Solution:")
     list3=[]
     list3.extend([list2[0],list2[1],nodes_ex,nodes_ex,nodes_ex,list2[-1]])
     print(list3)
     print("No path exist from source node 'A' to other nodes")
     print("No Solution")
  else:

    print("path exist from source node 'A' to other nodes"+" and Path is:")
    print list2
    print("Solution:")
    list3=[]
    list3.extend([list2[0],list2[1],nodes_ex,nodes_ex,nodes_ex,list2[-1]])
    print(list3)
    print("No path exist from source node 'A' to 'A'")
    print("No Solution")
  raw_input()
if __name__ == '__main__':
  graph= {  'A':['B','C','D'],
 	        'B':['A','D','C'],
 	        'C':['A','B','D','E'],
            'D':['A','B','C','E'],
            'E':['C','D'],
            }
  graph1= {  'A':['B','C','D'],
 	        'B':['A','D','C'],
 	        'C':['A','B','D','E'],
            'D':['A','B','C','E'],
            'E':['C','D']}
  graph2={'A':['B','C','D','F'],
          'B':['A','C','D','F'],
          'C':['A','B','D','E'],
          'D':['A','B','C','E'],
          'E':['C','D'],
          'F':['A','B'] }

  main()