import { configureStore } from '@reduxjs/toolkit';

// 暂时创建空的store，后续会添加具体的slice
export const store = configureStore({
  reducer: {
    // 这里会添加各种reducer
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;