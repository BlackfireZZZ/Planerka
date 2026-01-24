import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { authApi } from "../../api/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import axios from "axios";

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus("error");
        setMessage("Токен подтверждения не предоставлен.");
        return;
      }

      try {
        await authApi.verifyEmail(token);
        setStatus("success");
        // Перенаправление на страницу входа после успешного подтверждения
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      } catch (error) {
        setStatus("error");
        if (axios.isAxiosError(error) && error.response?.data?.detail) {
          setMessage(error.response.data.detail);
        } else {
          setMessage("Не удалось подтвердить email.");
        }
      }
    };

    verify();
  }, [token, navigate]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Подтверждение email</CardTitle>
        <CardDescription>Подтверждение вашего адреса электронной почты</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center py-6">
        {status === "loading" && (
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-500" />
            <p>Подтверждение...</p>
          </div>
        )}
        {status === "success" && (
          <div className="flex flex-col items-center space-y-4 text-green-600">
            <CheckCircle2 className="h-12 w-12" />
            <p className="text-lg font-medium">Email успешно подтвержден!</p>
          </div>
        )}
        {status === "error" && (
          <div className="flex flex-col items-center space-y-4 text-red-600">
            <XCircle className="h-12 w-12" />
            <p className="text-lg font-medium">Подтверждение не удалось</p>
            <Alert variant="destructive">
              <AlertTitle>Ошибка</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          </div>
        )}
      </CardContent>
      {status === "success" && (
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            Перенаправление на страницу входа...
          </p>
        </CardFooter>
      )}
      {status === "error" && (
        <CardFooter className="flex justify-center">
          <Link to="/login" className="text-blue-600 hover:underline">
            Перейти к входу
          </Link>
        </CardFooter>
      )}
    </Card>
  );
};
