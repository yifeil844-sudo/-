import Foundation
import HealthKit

@MainActor
class StepSimulator: ObservableObject {
    private let healthStore = HKHealthStore()
    private var timer: Timer?

    // Write a batch every 12 seconds — realistic granularity, battery friendly
    private let interval: TimeInterval = 12.0

    @Published var isRunning = false
    @Published var isAuthorized = false
    @Published var currentRate = 0       // steps/min shown in UI
    @Published var sessionSteps = 0
    @Published var authError: String?

    func requestAuthorization() {
        guard HKHealthStore.isHealthDataAvailable() else {
            authError = "此设备不支持 HealthKit"
            return
        }
        let stepType = HKQuantityType(.stepCount)
        healthStore.requestAuthorization(toShare: [stepType], read: []) { success, error in
            DispatchQueue.main.async {
                if success {
                    self.isAuthorized = true
                    self.authError = nil
                } else {
                    self.authError = error?.localizedDescription ?? "授权失败，请在"设置→健康"中允许写入步数"
                }
            }
        }
    }

    func start() {
        guard isAuthorized else {
            requestAuthorization()
            return
        }
        isRunning = true
        currentRate = Int.random(in: 160...185)
        // Write the first batch right away, then keep the timer running
        writeStepBatch()
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.writeStepBatch() }
        }
    }

    func stop() {
        isRunning = false
        timer?.invalidate()
        timer = nil
    }

    private func writeStepBatch() {
        // Steps for this interval, with ±10% natural variation
        let base = Double(currentRate) * (interval / 60.0)
        let steps = max(1, Int(base * Double.random(in: 0.90...1.10)))

        // Occasionally shift rate slightly so the average looks organic
        if Int.random(in: 0...4) == 0 {
            currentRate = Int.random(in: 155...188)
        }

        let endDate = Date()
        let startDate = endDate.addingTimeInterval(-interval)
        let stepType = HKQuantityType(.stepCount)
        let sample = HKQuantitySample(
            type: stepType,
            quantity: HKQuantity(unit: .count(), doubleValue: Double(steps)),
            start: startDate,
            end: endDate
        )

        healthStore.save(sample) { [weak self] success, _ in
            if success {
                Task { @MainActor in self?.sessionSteps += steps }
            }
        }
    }

    deinit { timer?.invalidate() }
}
