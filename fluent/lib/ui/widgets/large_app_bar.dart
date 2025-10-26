import 'package:flutter/material.dart';

class LargeAppBar extends StatelessWidget implements PreferredSizeWidget {
  const LargeAppBar({super.key, required this.title, this.subtitle, this.leadingIcon, this.actions});

  final Widget title;
  final Widget? subtitle;
  final Widget? leadingIcon;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Padding(
      padding: EdgeInsets.symmetric(horizontal: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (leadingIcon != null || (actions != null && actions!.isNotEmpty))
            Row(
              children: [if (leadingIcon != null) leadingIcon!, Spacer(), if (actions != null) ...actions!],
            ),
          Spacer(),
          Padding(
            padding: EdgeInsets.symmetric(
              horizontal: 14,
              vertical: 12,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                title,
                if (subtitle != null) subtitle!
              ],
            ),
          ),
        ],
      ),
    ),
  );

  @override
  Size get preferredSize => Size(double.infinity, 112 + (subtitle != null ? 24 : 0));
}
