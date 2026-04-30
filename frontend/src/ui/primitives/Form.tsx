import React from 'react';
import { View, ViewProps, Platform } from 'react-native';

export type FormProps = ViewProps & {
  onSubmit?: () => void;
};

export const Form = React.forwardRef<View, FormProps>(
  ({ onSubmit, children, style, ...props }, ref) => {
    if (Platform.OS === 'web') {
      const H5Form = 'form' as any;
      return (
        <H5Form
          onSubmit={(e: any) => {
            e.preventDefault();
            if (onSubmit) onSubmit();
          }}
          style={[{ display: 'flex', flexDirection: 'column' }, style as any]}
          {...props}
        >
          {children}
        </H5Form>
      );
    }

    return (
      <View ref={ref} style={style} {...props}>
        {children}
      </View>
    );
  }
);

Form.displayName = 'Form';
