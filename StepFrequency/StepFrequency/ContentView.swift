import SwiftUI

struct ContentView: View {
    @StateObject private var simulator = StepSimulator()

    var body: some View {
        VStack(spacing: 28) {
            Text("步频模拟器")
                .font(.largeTitle).fontWeight(.bold)
                .padding(.top, 40)

            // Status cards
            VStack(spacing: 10) {
                InfoRow(label: "状态",
                        value: simulator.isRunning ? "运行中 ✦" : "已停止",
                        valueColor: simulator.isRunning ? .green : .secondary)
                InfoRow(label: "当前步频",
                        value: simulator.isRunning ? "\(simulator.currentRate) 步/分钟" : "--",
                        valueColor: .blue)
                InfoRow(label: "本次累计",
                        value: "\(simulator.sessionSteps) 步")
            }
            .padding(.horizontal)

            // Error message
            if let err = simulator.authError {
                Text(err)
                    .font(.caption).foregroundColor(.red)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)
            }

            Spacer()

            // Big toggle button
            Button(action: toggle) {
                ZStack {
                    Circle()
                        .fill(simulator.isRunning ? Color.red : Color.green)
                        .frame(width: 180, height: 180)
                        .shadow(color: (simulator.isRunning ? Color.red : Color.green).opacity(0.4),
                                radius: 16, x: 0, y: 6)
                    VStack(spacing: 6) {
                        Image(systemName: simulator.isRunning ? "stop.fill" : "figure.walk")
                            .font(.system(size: 44))
                        Text(simulator.isRunning ? "停止" : "开始")
                            .font(.title2).fontWeight(.semibold)
                    }
                    .foregroundColor(.white)
                }
            }
            .buttonStyle(.plain)
            .animation(.spring(response: 0.3), value: simulator.isRunning)

            Spacer()

            // Auth button (shown only when not yet authorised)
            if !simulator.isAuthorized {
                Button("授权访问健康数据") {
                    simulator.requestAuthorization()
                }
                .buttonStyle(.bordered)
                .tint(.blue)
            }

            Text("请保持本 App 在前台运行\n支付宝运动会自动同步 Apple 健康中的步数")
                .font(.caption).foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
                .padding(.bottom, 30)
        }
        .onAppear { simulator.requestAuthorization() }
    }

    private func toggle() {
        simulator.isRunning ? simulator.stop() : simulator.start()
    }
}

private struct InfoRow: View {
    let label: String
    let value: String
    var valueColor: Color = .primary

    var body: some View {
        HStack {
            Text(label).foregroundColor(.secondary)
            Spacer()
            Text(value).fontWeight(.medium).foregroundColor(valueColor)
        }
        .padding(.horizontal, 16).padding(.vertical, 12)
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

#Preview {
    ContentView()
}
