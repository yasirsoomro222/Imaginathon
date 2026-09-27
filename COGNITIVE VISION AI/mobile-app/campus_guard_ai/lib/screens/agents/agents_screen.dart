import 'package:flutter/material.dart';

class AgentsScreen extends StatelessWidget {
  const AgentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AI Agents"),
        centerTitle: true,
      ),

      body: Padding(
        padding: const EdgeInsets.all(16),

        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              // Main AI Agent Card
              Card(
                elevation: 4,

                child: ListTile(

                  leading: const CircleAvatar(
                    radius: 25,

                    child: Icon(
                      Icons.smart_toy,
                      size: 30,
                    ),
                  ),


                  title: const Text(
                    "Cognitive Vision Agent",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),


                  subtitle: const Text(
                    "AI Surveillance System",
                  ),


                  trailing: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),

                    decoration: BoxDecoration(
                      color: Colors.green,
                      borderRadius: BorderRadius.circular(20),
                    ),


                    child: const Text(
                      "Active",
                      style: TextStyle(
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),


              const SizedBox(height: 25),



              const Text(
                "Detection Agents",

                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),



              const SizedBox(height: 12),



              agentCard(
                "ID Card Detection Agent",
                Icons.badge,
                "Running",
              ),

              agentCard(
                "Smoking Detection Agent",
                Icons.smoking_rooms,
                "Running",
              ),


             

            ],
          ),
        ),
      ),
    );
  }




  Widget agentCard(
      String title,
      IconData icon,
      String status,
      ) {


    return Card(

      margin: const EdgeInsets.only(
        bottom: 12,
      ),


      child: ListTile(

        leading: Icon(
          icon,
          size: 30,
        ),


        title: Text(
          title,

          style: const TextStyle(
            fontWeight: FontWeight.w600,
          ),
        ),


        subtitle: Text(
          status,
        ),


        trailing: Icon(
          status == "Running"
              ? Icons.check_circle
              : Icons.pause_circle,

          color: status == "Running"
              ? Colors.green
              : Colors.orange,
        ),
      ),
    );
  }
}