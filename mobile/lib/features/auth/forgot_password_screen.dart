import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/common_views.dart';
import 'forgot_password_controller.dart';

/// Two-step password recovery: request an OTP by mobile, then set a new
/// password. Never fakes SMS/OTP delivery — in development mock mode the
/// backend returns the code so the flow is testable end to end.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _mobileController = TextEditingController();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _mobileController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  Future<void> _sendOtp(ForgotPasswordController controller) async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    final ok = await controller.requestOtp(_mobileController.text.trim());
    if (ok && mounted) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          const SnackBar(content: Text(AppStrings.otpSent)),
        );
    }
  }

  Future<void> _reset(ForgotPasswordController controller) async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    await controller.resetPassword(
      code: _codeController.text.trim(),
      newPassword: _passwordController.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<ForgotPasswordController>();
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.forgotPasswordTitle)),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: switch (controller.step) {
                ForgotPasswordStep.done => _DoneView(
                    onLogin: () => Navigator.of(context).pop(true),
                  ),
                _ => _buildForm(controller),
              },
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildForm(ForgotPasswordController controller) {
    final theme = Theme.of(context);
    final submittingOtp = controller.step == ForgotPasswordStep.enterMobile &&
        controller.isLoading;
    final submittingReset = controller.step == ForgotPasswordStep.resetting &&
        controller.isLoading;

    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            AppStrings.forgotPasswordHint,
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 20),
          if (controller.errorMessage != null) ...[
            ErrorBanner(message: controller.errorMessage!),
            const SizedBox(height: 16),
          ],
          if (controller.infoMessage != null) ...[
            InfoBanner(message: controller.infoMessage!),
            const SizedBox(height: 16),
          ],
          TextFormField(
            controller: _mobileController,
            enabled: controller.step == ForgotPasswordStep.enterMobile,
            keyboardType: TextInputType.phone,
            maxLength: 10,
            textInputAction: TextInputAction.done,
            decoration: const InputDecoration(
              labelText: AppStrings.mobileNumberLabel,
              hintText: AppStrings.mobileHint,
              prefixIcon: Icon(Icons.phone_outlined),
            ),
            validator: (value) {
              final v = (value ?? '').trim();
              if (v.isEmpty) return AppStrings.mobileNumberLabel;
              if (v.length != 10 || int.tryParse(v) == null) {
                return AppStrings.mobileInvalid;
              }
              return null;
            },
            onFieldSubmitted: controller.step == ForgotPasswordStep.enterMobile
                ? (_) => _sendOtp(controller)
                : null,
          ),
          const SizedBox(height: 16),
          if (controller.step == ForgotPasswordStep.resetting) ...[
            TextFormField(
              controller: _codeController,
              keyboardType: TextInputType.number,
              maxLength: 6,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: AppStrings.otpLabel,
                hintText: AppStrings.otpHint,
                prefixIcon: Icon(Icons.password_outlined),
              ),
              validator: (value) =>
                  (value == null || value.trim().isEmpty)
                      ? AppStrings.otpRequired
                      : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _passwordController,
              obscureText: _obscurePassword,
              textInputAction: TextInputAction.next,
              decoration: InputDecoration(
                labelText: AppStrings.newPasswordLabel,
                prefixIcon: const Icon(Icons.lock_outline),
                suffixIcon: IconButton(
                  icon: Icon(_obscurePassword
                      ? Icons.visibility_off
                      : Icons.visibility),
                  onPressed: () =>
                      setState(() => _obscurePassword = !_obscurePassword),
                ),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return AppStrings.passwordRequired;
                }
                if (value.length < 6) return AppStrings.passwordMinLength;
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _confirmController,
              obscureText: _obscurePassword,
              textInputAction: TextInputAction.done,
              onFieldSubmitted: (_) => _reset(controller),
              decoration: const InputDecoration(
                labelText: AppStrings.confirmPasswordLabel,
                prefixIcon: Icon(Icons.lock_outline),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return AppStrings.confirmPasswordRequired;
                }
                if (value != _passwordController.text) {
                  return AppStrings.passwordsMismatch;
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed:
                  submittingReset ? null : () => _reset(controller),
              child: submittingReset
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text(AppStrings.resetPasswordButton),
            ),
          ] else ...[
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: submittingOtp ? null : () => _sendOtp(controller),
              child: submittingOtp
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text(AppStrings.sendOtpButton),
            ),
          ],
        ],
      ),
    );
  }
}

class _DoneView extends StatelessWidget {
  const _DoneView({required this.onLogin});

  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.check_circle_outline,
            size: 72, color: AppTheme.primaryGreen),
        const SizedBox(height: 16),
        Text(
          AppStrings.passwordResetSuccess,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: onLogin,
          child: const Text(AppStrings.backToLogin),
        ),
      ],
    );
  }
}