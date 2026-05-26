import { useMemo } from "react";
import { View } from "react-native";

type TotpQrCodeProps = {
  uri?: string | null;
};

type QRCodeInstance = {
  addData: (data: string) => void;
  make: () => void;
  getModuleCount: () => number;
  isDark: (row: number, col: number) => boolean;
};

type QRCodeConstructor = new (
  typeNumber: number,
  errorCorrectLevel: number,
) => QRCodeInstance;

const QRCode = require("qrcode-terminal/vendor/QRCode") as QRCodeConstructor;
const QRErrorCorrectLevel =
  require("qrcode-terminal/vendor/QRCode/QRErrorCorrectLevel") as { M: number };

function createQrModules(value: string) {
  const qr = new QRCode(-1, QRErrorCorrectLevel.M);
  qr.addData(value);
  qr.make();

  const moduleCount = qr.getModuleCount();
  const quietZone = 4;
  const size = moduleCount + quietZone * 2;
  const darkModules: { x: number; y: number }[] = [];

  for (let row = 0; row < moduleCount; row += 1) {
    for (let col = 0; col < moduleCount; col += 1) {
      if (qr.isDark(row, col)) {
        darkModules.push({ x: col + quietZone, y: row + quietZone });
      }
    }
  }

  return { size, darkModules };
}

/**
 * Renderuje QR code TOTP lokalnie w przeglądarce.
 */
export function TotpQrCode({ uri }: TotpQrCodeProps) {
  const qr = useMemo(() => (uri ? createQrModules(uri) : null), [uri]);

  if (!uri) return null;

  return (
    <View className="items-start">
      <svg
        aria-label="Kod QR do konfiguracji MFA"
        height={192}
        role="img"
        shapeRendering="crispEdges"
        style={{ border: "1px solid #e5e5e5", borderRadius: 6 }}
        viewBox={`0 0 ${qr?.size ?? 1} ${qr?.size ?? 1}`}
        width={192}
      >
        <rect fill="#ffffff" height={qr?.size ?? 1} width={qr?.size ?? 1} />
        <g fill="#171717">
          {qr?.darkModules.map((module) => (
            <rect
              height="1"
              key={`${module.x}-${module.y}`}
              width="1"
              x={module.x}
              y={module.y}
            />
          ))}
        </g>
      </svg>
    </View>
  );
}
