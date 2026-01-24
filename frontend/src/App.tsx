import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { AuthLayout } from "./layouts/AuthLayout";
import { MainLayout } from "./layouts/MainLayout";
import { ProtectedRoutes } from "./layouts/ProtectedRoutes";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { VerifyEmailPage } from "./pages/auth/VerifyEmailPage";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/auth/ResetPasswordPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { InstitutionsPage } from "./pages/institutions/InstitutionsPage";
import { CreateInstitutionPage } from "./pages/institutions/CreateInstitutionPage";
import { InstitutionDetailPage } from "./pages/institutions/InstitutionDetailPage";
import { SchedulesPage } from "./pages/schedules/SchedulesPage";
import { ScheduleDetailPage } from "./pages/schedules/ScheduleDetailPage";
import { CreateSchedulePage } from "./pages/schedules/CreateSchedulePage";
import { CreateClassGroupPage } from "./pages/class-groups/CreateClassGroupPage";
import { CreateLessonPage } from "./pages/lessons/CreateLessonPage";
import { CreateRoomPage } from "./pages/rooms/CreateRoomPage";
import { CreateTimeSlotPage } from "./pages/time-slots/CreateTimeSlotPage";
import { CreateTeacherPage } from "./pages/teachers/CreateTeacherPage";
import { CreateStudentPage } from "./pages/students/CreateStudentPage";

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Публичные маршруты аутентификации */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
          </Route>

          {/* Защищенные маршруты */}
          <Route element={<ProtectedRoutes />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/institutions" element={<InstitutionsPage />} />
              <Route
                path="/institutions/new"
                element={<CreateInstitutionPage />}
              />
              <Route
                path="/institutions/:institutionId"
                element={<InstitutionDetailPage />}
              />
              <Route path="/schedules" element={<SchedulesPage />} />
              <Route path="/schedules/new" element={<CreateSchedulePage />} />
              <Route
                path="/schedules/:scheduleId"
                element={<ScheduleDetailPage />}
              />
              <Route
                path="/class-groups/new"
                element={<CreateClassGroupPage />}
              />
              <Route path="/lessons/new" element={<CreateLessonPage />} />
              <Route path="/rooms/new" element={<CreateRoomPage />} />
              <Route path="/time-slots/new" element={<CreateTimeSlotPage />} />
              <Route path="/teachers/new" element={<CreateTeacherPage />} />
              <Route path="/students/new" element={<CreateStudentPage />} />
            </Route>
          </Route>

          {/* Перехват всех остальных маршрутов */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
