declare module "qrcode-terminal/vendor/QRCode" {
  type QRCodeInstance = {
    addData: (data: string) => void;
    make: () => void;
    getModuleCount: () => number;
    isDark: (row: number, col: number) => boolean;
  };

  const QRCode: new (
    typeNumber: number,
    errorCorrectLevel: number,
  ) => QRCodeInstance;

  export = QRCode;
}

declare module "qrcode-terminal/vendor/QRCode/QRErrorCorrectLevel" {
  const QRErrorCorrectLevel: {
    L: number;
    M: number;
    Q: number;
    H: number;
  };

  export = QRErrorCorrectLevel;
}
