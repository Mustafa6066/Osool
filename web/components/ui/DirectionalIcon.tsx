import { ElementType } from 'react';
import { LucideIcon } from 'lucide-react';

interface DirectionalIconProps {
  icon: ElementType | LucideIcon;
  className?: string;
  [key: string]: any;
}

export function DirectionalIcon({ icon: Icon, className = '', ...props }: DirectionalIconProps) {
  return <Icon className={`rtl:rotate-180 ${className}`} {...props} />;
}
