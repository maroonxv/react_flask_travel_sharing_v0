import styles from './Card.module.css';

const Card = ({ children, className = '', contentClassName = '', title, action }) => {
    return (
        <div className={`${styles.card} ${className}`}>
            {(title || action) && (
                <div className={styles.header}>
                    {title && <h3 className={styles.title}>{title}</h3>}
                    {action && <div className={styles.action}>{action}</div>}
                </div>
            )}
            <div className={`${styles.content} ${contentClassName}`}>
                {children}
            </div>
        </div>
    );
};

export default Card;
