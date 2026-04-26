const path = require("path");

exports.default = async function afterPack(context) {
  if (context.electronPlatformName !== "win32") {
    return;
  }

  const { flipFuses, FuseVersion, FuseV1Options } = await import("@electron/fuses");
  const executablePath = path.join(
    context.appOutDir,
    `${context.packager.appInfo.productFilename}.exe`
  );

  await flipFuses(executablePath, {
    version: FuseVersion.V1,
    [FuseV1Options.RunAsNode]: false,
    [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
    [FuseV1Options.EnableNodeCliInspectArguments]: false
  });
};
