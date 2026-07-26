import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ExamPredictorApp());
}

class ExamPredictorApp extends StatelessWidget {
  const ExamPredictorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Exam Score Predictor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const PredictionForm(),
    );
  }
}

class PredictionForm extends StatefulWidget {
  const PredictionForm({super.key});

  @override
  State<PredictionForm> createState() => _PredictionFormState();
}

class _PredictionFormState extends State<PredictionForm> {
  //  RENDER URL

  final String apiUrl =
      'https://student-predictor-api-9ds9.onrender.com/api/v1/predict';

  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;
  String _resultMessage = '';
  bool _isError = false;

  // Controllers
  final ageController = TextEditingController();
  final studyHoursController = TextEditingController();
  final sleepHoursController = TextEditingController();
  final socialMediaController = TextEditingController();
  final netflixController = TextEditingController();
  final attendanceController = TextEditingController();
  final exerciseController = TextEditingController();
  final mentalHealthController = TextEditingController();

  // Dropdowns
  String? selectedGender;
  String? selectedExtra;
  String? selectedJob;
  String? selectedDiet;
  String? selectedParental;
  String? selectedInternet;

  @override
  void dispose() {
    ageController.dispose();
    studyHoursController.dispose();
    sleepHoursController.dispose();
    socialMediaController.dispose();
    netflixController.dispose();
    attendanceController.dispose();
    exerciseController.dispose();
    mentalHealthController.dispose();
    super.dispose();
  }

  Future<void> _predictScore() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _resultMessage = '';
    });

    final body = {
      "age": int.parse(ageController.text),
      "gender": selectedGender,
      "study_hours_per_day": double.parse(studyHoursController.text),
      "sleep_hours": double.parse(sleepHoursController.text),
      "social_media_hours": double.parse(socialMediaController.text),
      "netflix_hours": double.parse(netflixController.text),
      "attendance_percentage": double.parse(attendanceController.text),
      "exercise_frequency": int.parse(exerciseController.text),
      "mental_health_rating": int.parse(mentalHealthController.text),
      "extracurricular_participation": selectedExtra,
      "part_time_job": selectedJob,
      "diet_quality": selectedDiet,
      "parental_education_level": selectedParental,
      "internet_quality": selectedInternet,
    };

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _resultMessage = data['predicted_exam_score'].toStringAsFixed(2);
          _isError = false;
        });
      } else {
        final errorData = jsonDecode(response.body);
        setState(() {
          _resultMessage = errorData['detail'][0]['msg'];
          _isError = true;
        });
      }
    } catch (e) {
      setState(() {
        _resultMessage = "Connection failed. Check internet or API URL.";
        _isError = true;
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // --- VISUAL UI HELPERS ---

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 16.0, bottom: 8.0),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: Colors.deepPurple.shade700,
        ),
      ),
    );
  }

  Widget _buildCustomTextField({
    required String label,
    required String hint,
    required TextEditingController controller,
    required IconData icon,
    bool isDecimal = true,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: TextFormField(
        controller: controller,
        keyboardType: isDecimal
            ? const TextInputType.numberWithOptions(decimal: true)
            : TextInputType.number,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          prefixIcon: Icon(icon, color: Colors.deepPurple.shade400),
          filled: true,
          fillColor: Colors.grey.shade100,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300, width: 1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.deepPurple.shade400, width: 2),
          ),
        ),
        validator: (value) {
          if (value == null || value.isEmpty) return 'Required';
          if (isDecimal && double.tryParse(value) == null) return 'Invalid';
          if (!isDecimal && int.tryParse(value) == null) return 'Invalid';
          return null;
        },
      ),
    );
  }

  Widget _buildCustomDropdown({
    required String label,
    required List<String> items,
    required String? value,
    required Function(String?) onChanged,
    required IconData icon,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: DropdownButtonFormField<String>(
        value: value,
        icon:
            const Icon(Icons.arrow_drop_down_circle, color: Colors.deepPurple),
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: Colors.deepPurple.shade400),
          filled: true,
          fillColor: Colors.grey.shade100,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300, width: 1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.deepPurple.shade400, width: 2),
          ),
        ),
        items: items.map((String val) {
          return DropdownMenuItem(value: val, child: Text(val));
        }).toList(),
        onChanged: onChanged,
        validator: (val) => val == null ? 'Required' : null,
      ),
    );
  }

  // --- MAIN BUILD ---
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('AcademIQ',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 10.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // --- ACADEMIC HABITS ---
              _buildSectionTitle('📚 Academic Habits'),
              _buildCustomTextField(
                  label: 'Study Hours / Day',
                  hint: '0 - 15',
                  controller: studyHoursController,
                  icon: Icons.book_outlined),
              _buildCustomTextField(
                  label: 'Attendance %',
                  hint: '0 - 100',
                  controller: attendanceController,
                  icon: Icons.how_to_reg_outlined),
              _buildCustomDropdown(
                  label: 'Extracurricular',
                  items: ["Yes", "No"],
                  value: selectedExtra,
                  onChanged: (v) => setState(() => selectedExtra = v),
                  icon: Icons.sports_soccer),

              // --- LIFESTYLE & HEALTH ---
              _buildSectionTitle('🏃 Lifestyle & Health'),
              _buildCustomTextField(
                  label: 'Sleep Hours / Night',
                  hint: '0 - 12',
                  controller: sleepHoursController,
                  icon: Icons.bedtime_outlined),
              _buildCustomTextField(
                  label: 'Exercise (days/week)',
                  hint: '0 - 7',
                  controller: exerciseController,
                  icon: Icons.fitness_center_outlined,
                  isDecimal: false),
              _buildCustomTextField(
                  label: 'Mental Health Rating',
                  hint: '1 - 10',
                  controller: mentalHealthController,
                  icon: Icons.psychology_outlined,
                  isDecimal: false),
              _buildCustomDropdown(
                  label: 'Diet Quality',
                  items: ["Poor", "Fair", "Good", "Excellent"],
                  value: selectedDiet,
                  onChanged: (v) => setState(() => selectedDiet = v),
                  icon: Icons.restaurant_menu_outlined),

              // --- DIGITAL HABITS ---
              _buildSectionTitle('📱 Digital Habits'),
              _buildCustomTextField(
                  label: 'Social Media Hours',
                  hint: '0 - 15',
                  controller: socialMediaController,
                  icon: Icons.smartphone_outlined),
              _buildCustomTextField(
                  label: 'Netflix Hours',
                  hint: '0 - 15',
                  controller: netflixController,
                  icon: Icons.live_tv_outlined),
              _buildCustomDropdown(
                  label: 'Internet Quality',
                  items: ["Poor", "Average", "Good"],
                  value: selectedInternet,
                  onChanged: (v) => setState(() => selectedInternet = v),
                  icon: Icons.wifi_outlined),
              _buildCustomDropdown(
                  label: 'Part-Time Job',
                  items: ["Yes", "No"],
                  value: selectedJob,
                  onChanged: (v) => setState(() => selectedJob = v),
                  icon: Icons.work_outline),

              // --- DEMOGRAPHICS ---
              _buildSectionTitle('👤 Demographics'),
              _buildCustomTextField(
                  label: 'Age',
                  hint: '16 - 30',
                  controller: ageController,
                  icon: Icons.cake_outlined,
                  isDecimal: false),
              _buildCustomDropdown(
                  label: 'Gender',
                  items: ["Male", "Female", "Other"],
                  value: selectedGender,
                  onChanged: (v) => setState(() => selectedGender = v),
                  icon: Icons.person_outline),
              _buildCustomDropdown(
                  label: 'Parental Education',
                  items: ["None", "High School", "Bachelor", "Master"],
                  value: selectedParental,
                  onChanged: (v) => setState(() => selectedParental = v),
                  icon: Icons.school_outlined),

              const SizedBox(height: 30),

              // --- SUBMIT BUTTON ---
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.deepPurple.shade400,
                      Colors.indigo.shade500
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.deepPurple.withOpacity(0.3),
                      blurRadius: 10,
                      spreadRadius: 2,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _predictScore,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Predict My Score',
                          style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.white)),
                ),
              ),

              const SizedBox(height: 24),

              // --- RESULT DISPLAY ---
              if (_resultMessage.isNotEmpty)
                AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: _isError
                        ? LinearGradient(
                            colors: [Colors.red.shade100, Colors.red.shade50])
                        : LinearGradient(colors: [
                            Colors.green.shade100,
                            Colors.green.shade50
                          ]),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                        color: _isError
                            ? Colors.red.shade300
                            : Colors.green.shade300,
                        width: 2),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        _isError
                            ? Icons.error_outline
                            : Icons.emoji_events_outlined,
                        size: 40,
                        color: _isError
                            ? Colors.red.shade700
                            : Colors.green.shade700,
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _isError ? "Error" : "Your Predicted Score",
                        style: TextStyle(
                            fontSize: 16,
                            color: _isError
                                ? Colors.red.shade700
                                : Colors.green.shade800,
                            fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        _isError ? _resultMessage : "$_resultMessage / 100",
                        style: TextStyle(
                          fontSize: _isError ? 16 : 36,
                          fontWeight: FontWeight.bold,
                          color: _isError
                              ? Colors.red.shade900
                              : Colors.green.shade900,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 40), // Bottom padding for scrolling
            ],
          ),
        ),
      ),
    );
  }
}
