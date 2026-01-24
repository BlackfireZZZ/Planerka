import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { institutionsApi } from "@/api/institutions";
import type { Institution } from "@/api/institutions";

export const InstitutionsPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInstitutions();
  }, []);

  const loadInstitutions = async () => {
    try {
      setLoading(true);
      const data = await institutionsApi.list();
      setInstitutions(data);
    } catch (error) {
      console.error("Failed to load institutions:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Загрузка...</div>;
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Учреждения</h1>
        <Button asChild>
          <Link to="/institutions/new">
            <Plus className="mr-2 h-4 w-4" />
            Создать учреждение
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {institutions.map((institution) => (
          <Card key={institution.id} className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <Building2 className="h-8 w-8 text-blue-500" />
                <div>
                  <h3 className="font-semibold text-lg">{institution.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    Создано:{" "}
                    {new Date(institution.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <Link to={`/institutions/${institution.id}`}>
                <Button variant="outline" className="w-full">
                  Открыть
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>

      {institutions.length === 0 && (
        <Card className="p-12 text-center">
          <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">Нет учреждений</p>
          <Button asChild>
            <Link to="/institutions/new">Создать первое учреждение</Link>
          </Button>
        </Card>
      )}
    </div>
  );
};
