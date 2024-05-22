import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'dart:convert';
import 'package:url_launcher/url_launcher.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Job Listings',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key});

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  Future<List<Job>>? jobs;
  int displayedItemsCount = 30;
  String? _jenisPekerjaanValue;
  final TextEditingController _startDateController = TextEditingController();
  final TextEditingController _endDateController = TextEditingController();
  final TextEditingController _lokasiController = TextEditingController();
  final TextEditingController _perusahaanController = TextEditingController();

  @override
  void initState() {
    super.initState();
    jobs = fetchJobs();
  }

  Future<List<Job>> fetchJobs([
    String? jenisPekerjaan,
    String? dariTanggal,
    String? sampaiTanggal,
    String? lokasi,
    String? perusahaan,
  ]) async {
    final Map<String, String> queryParameters = {};

    if (jenisPekerjaan != null) {
      queryParameters["jenis_pekerjaan"] = jenisPekerjaan;
    }
    if (dariTanggal != null && dariTanggal.isNotEmpty) {
      queryParameters["dari_tanggal"] = dariTanggal;
    }
    if (sampaiTanggal != null && sampaiTanggal.isNotEmpty) {
      queryParameters["sampai_tanggal"] = sampaiTanggal;
    }
    if (lokasi != null && lokasi.isNotEmpty) {
      queryParameters["lokasi"] = lokasi;
    }
    if (perusahaan != null && perusahaan.isNotEmpty) {
      queryParameters["perusahaan"] = perusahaan;
    }

    final response =
        await http.get(Uri.http('34.67.253.129:5001', '/api', queryParameters));

    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((job) => Job.fromJson(job)).toList();
    } else {
      throw Exception('Failed to load jobs');
    }
  }

  void showMore() {
    setState(() {
      displayedItemsCount += 30;
    });
  }

  Future<void> _selectStartDate() async {
    DateTime? picked = await showDatePicker(
        context: context,
        initialDate: DateTime.now(),
        firstDate: DateTime(2000),
        lastDate: DateTime(2100));

    if (picked != null) {
      setState(() {
        _startDateController.text = picked.toString().split(" ")[0];
      });
    }
  }

  Future<void> _selectEndDate() async {
    DateTime? picked = await showDatePicker(
        context: context,
        initialDate: DateTime.now(),
        firstDate: DateTime(2000),
        lastDate: DateTime(2100));

    if (picked != null) {
      setState(() {
        _endDateController.text = picked.toString().split(" ")[0];
      });
    }
  }

  String formatDate(String dateString) {
    // Define the date format matching your input string
    DateFormat inputFormat = DateFormat('EEE, dd MMM yyyy HH:mm:ss \'GMT\'');

    // Parse the input date string
    DateTime dateTime = inputFormat.parseUTC(dateString).toLocal();

    // Format the date to "dd MMMM yyyy"
    String formattedDate = DateFormat('dd MMMM yyyy').format(dateTime);

    // Calculate time ago
    String timeAgo = timeAgoSinceDate(dateTime);

    // Combine formatted date and time ago
    return "$formattedDate ($timeAgo ago)";
  }


  String timeAgoSinceDate(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays >= 365) {
      final years = (difference.inDays / 365).floor();
      return "$years ${years == 1 ? 'year' : 'years'}";
    } else if (difference.inDays >= 30) {
      final months = (difference.inDays / 30).floor();
      return "$months ${months == 1 ? 'month' : 'months'}";
    } else if (difference.inDays >= 1) {
      return "${difference.inDays} ${difference.inDays == 1 ? 'day' : 'days'}";
    } else if (difference.inHours >= 1) {
      return "${difference.inHours} ${difference.inHours == 1 ? 'hour' : 'hours'}";
    } else if (difference.inMinutes >= 1) {
      return "${difference.inMinutes} ${difference.inMinutes == 1 ? 'minute' : 'minutes'}";
    } else {
      return "${difference.inSeconds} ${difference.inSeconds == 1 ? 'second' : 'seconds'}";
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Job Listings',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
        backgroundColor: Colors.blueAccent,
        elevation: 10,
        shadowColor: Colors.black.withOpacity(0.5),
      ),
      body: Center(
        child: FutureBuilder<List<Job>>(
          future: jobs,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const CircularProgressIndicator();
            } else if (snapshot.hasError) {
              return Text("${snapshot.error}");
            } else if (snapshot.hasData) {
              List<Job>? jobs = snapshot.data;
              return ListView.builder(
                itemCount: (displayedItemsCount < jobs!.length)
                    ? displayedItemsCount + 1
                    : jobs.isNotEmpty
                        ? jobs.length
                        : 1,
                itemBuilder: (context, index) {
                  if (jobs.isEmpty) {
                    return const Text('No data available');
                  }
                  if (index == displayedItemsCount) {
                    return Center(
                      child: ElevatedButton(
                        onPressed: showMore,
                        child: const Text('Show More'),
                      ),
                    );
                  }

                  return Card(
                    margin: const EdgeInsets.all(10.0),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(15.0),
                    ),
                    elevation: 5,
                    shadowColor: Colors.blueAccent.withOpacity(0.2),
                    child: ListTile(
                      contentPadding: const EdgeInsets.all(15.0),
                      title: Text(
                        jobs[index].judulLowongan,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: Colors.black87,
                        ),
                      ),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 10),
                          Text(
                            'Company: ${jobs[index].perusahaan}',
                            style: const TextStyle(
                                color: Colors.black87, fontSize: 14),
                          ),
                          Text(
                            'Location: ${jobs[index].lokasiPekerjaan}',
                            style: const TextStyle(
                                color: Colors.black87, fontSize: 14),
                          ),
                          Text(
                            'Published: ${formatDate(jobs[index].tanggalPublikasi)}',
                            style: const TextStyle(
                                color: Colors.black87, fontSize: 14),
                          ),
                          Text(
                            'Source: ${jobs[index].sumberSitus}',
                            style: const TextStyle(
                                color: Colors.black87, fontSize: 14),
                          ),
                        ],
                      ),
                      onTap: () {
                        _launchURL(jobs[index].linkLowongan);
                      },
                    ),
                  );
                },
              );
            } else {
              return const Text('No data available');
            }
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          showModalBottomSheet(
            isScrollControlled: true,
            context: context,
            builder: (BuildContext context) {
              return Padding(
                  padding: EdgeInsets.only(
                    bottom: MediaQuery.of(context).viewInsets.bottom,
                  ),
                  child: SingleChildScrollView(
                      child: Padding(
                          padding: const EdgeInsets.all(20.0),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Stack(children: <Widget>[
                                const Center(
                                    child: Text(
                                  'Search Jobs',
                                  style: TextStyle(
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                  ),
                                )),
                                Container(
                                  alignment: Alignment.centerRight,
                                  child: IconButton(
                                    icon: const Icon(Icons.close),
                                    onPressed: () {
                                      Navigator.pop(context); // Close the modal
                                    },
                                  ),
                                )
                              ]),
                              const SizedBox(height: 20),
                              DropdownButtonFormField<String>(
                                value: _jenisPekerjaanValue,
                                onChanged: (newValue) {
                                  setState(() {
                                    _jenisPekerjaanValue = newValue!;
                                  });
                                },
                                items: <String>[
                                  'Programmer',
                                  'Data',
                                  'Cyber Security',
                                  'Network',
                                ].map<DropdownMenuItem<String>>((String value) {
                                  return DropdownMenuItem<String>(
                                    value: value,
                                    child: Text(value),
                                  );
                                }).toList(),
                                decoration: InputDecoration(
                                  labelText: 'Jenis Pekerjaan',
                                  border: const OutlineInputBorder(),
                                  suffixIcon: _jenisPekerjaanValue == null
                                      ? null
                                      : IconButton(
                                          icon: const Icon(Icons.clear),
                                          onPressed: () => setState(() {
                                                _jenisPekerjaanValue = null;
                                              })),
                                ),
                              ),
                              const SizedBox(height: 20),
                              Row(
                                children: [
                                  Expanded(
                                      child: TextField(
                                          controller: _startDateController,
                                          decoration: const InputDecoration(
                                              labelText: 'From',
                                              filled: true,
                                              prefixIcon:
                                                  Icon(Icons.calendar_today),
                                              enabledBorder: OutlineInputBorder(
                                                  borderSide: BorderSide.none),
                                              focusedBorder: OutlineInputBorder(
                                                  borderSide: BorderSide(
                                                      color: Colors.blue))),
                                          readOnly: true,
                                          onTap: () {
                                            _selectStartDate();
                                          })),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: TextField(
                                        controller: _endDateController,
                                        decoration: const InputDecoration(
                                            labelText: 'To',
                                            filled: true,
                                            prefixIcon:
                                                Icon(Icons.calendar_today),
                                            enabledBorder: OutlineInputBorder(
                                                borderSide: BorderSide.none),
                                            focusedBorder: OutlineInputBorder(
                                                borderSide: BorderSide(
                                                    color: Colors.blue))),
                                        readOnly: true,
                                        onTap: () {
                                          _selectEndDate();
                                        }),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              TextFormField(
                                controller: _lokasiController,
                                decoration: InputDecoration(
                                  labelText: 'Lokasi',
                                  border: const OutlineInputBorder(),
                                  suffixIcon: IconButton(
                                    onPressed: _lokasiController.clear,
                                    icon: const Icon(Icons.clear),
                                  ),
                                ),
                                onChanged: (value) {
                                  _lokasiController.text = value;
                                },
                              ),
                              const SizedBox(height: 20),
                              TextFormField(
                                controller: _perusahaanController,
                                decoration: InputDecoration(
                                    labelText: 'Perusahaan Penyedia',
                                    border: const OutlineInputBorder(),
                                    suffixIcon: IconButton(
                                      onPressed: _perusahaanController.clear,
                                      icon: const Icon(Icons.clear),
                                    )),
                                onChanged: (value) {
                                  _perusahaanController.text = value;
                                },
                              ),
                              const SizedBox(height: 20),
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  ElevatedButton(
                                    onPressed: () {
                                      // Add clear logic here
                                      _startDateController.clear();
                                      _endDateController.clear();
                                      _lokasiController.clear();
                                      _perusahaanController.clear();
                                      setState(() {
                                        _jenisPekerjaanValue = null;
                                      }); // Refresh the state to update the UI
                                      jobs = fetchJobs();
                                      Navigator.pop(context);
                                    },
                                    child: const Text('Reset'),
                                  ),
                                  ElevatedButton(
                                    onPressed: () {
                                      setState(() {});
                                      jobs = fetchJobs(
                                          _jenisPekerjaanValue?.toLowerCase(),
                                          _startDateController.text,
                                          _endDateController.text,
                                          _lokasiController.text,
                                          _perusahaanController.text);
                                      Navigator.pop(context);
                                    },
                                    child: const Text('Search'),
                                  ),
                                ],
                              )
                            ],
                          ))));
            },
          );
        },
        child: const Icon(Icons.search),
      ),
    );
  }

  void _launchURL(Uri url) async {
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      throw 'Could not launch $url';
    }
  }
}

class Job {
  final String jenisPekerjaan;
  final String judulLowongan;
  final Uri linkLowongan;
  final String lokasiPekerjaan;
  final String perusahaan;
  final String sumberSitus;
  final String tanggalPublikasi;

  Job({
    required this.jenisPekerjaan,
    required this.judulLowongan,
    required this.linkLowongan,
    required this.lokasiPekerjaan,
    required this.perusahaan,
    required this.sumberSitus,
    required this.tanggalPublikasi,
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      jenisPekerjaan: json['jenis_pekerjaan'],
      judulLowongan: json['judul_lowongan'],
      linkLowongan: Uri.parse(json['link_lowongan']),
      lokasiPekerjaan: json['lokasi_pekerjaan'],
      perusahaan: json['perusahaan'],
      sumberSitus: json['sumber_situs'],
      tanggalPublikasi: json['tanggal_publikasi'],
    );
  }
}
