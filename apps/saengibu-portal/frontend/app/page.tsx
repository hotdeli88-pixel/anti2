export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <div className="max-w-xl text-center">
        <h1 className="text-3xl font-semibold">saengibu-portal</h1>
        <p className="mt-4 text-gray-600">
          학교생활기록부 포털. 교사가 먼저 쓰고, AI가 피드백합니다.
        </p>
        <p className="mt-2 text-sm text-gray-500">
          초기 스캐폴딩 상태. 인증/에디터/대시보드는 M0 이후 추가됩니다.
        </p>
      </div>
    </main>
  );
}
