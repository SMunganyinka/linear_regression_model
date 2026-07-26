import 'package:flutter_test/flutter_test.dart';
import 'package:academiq/main.dart';

void main() {
  testWidgets('AcademIQ app loads successfully', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const ExamPredictorApp());

    // Verify that the main title renders
    expect(find.text('AcademIQ'), findsOneWidget);

    // Verify that the submit button renders
    expect(find.text('Predict My Score'), findsOneWidget);
  });
}
